import json
import boto3
import botocore
import botocore.exceptions as excep
import logging
import io
import os
import time
import codecs
from zipfile import ZipFile

logger = logging.getLogger()
logger.setLevel(logging.INFO)

deployment_config_path = "scripts/deploy-config.json"
repo_analysis_path = "analysis/"
target_aws_account_id = ''
zipfile = ''

codecommit = boto3.client('codecommit')
pipeline = boto3.client('codepipeline')
quicksight = None
s3 = boto3.resource('s3')
roleArn = None
sessionName = 'CrossAccountQuickSightSession'

def get_manifest_file(repository_name, commit_id):
    response = codecommit.get_file(repositoryName = repository_name, commitSpecifier = commit_id, filePath = deployment_config_path)
    print(str(response))
    logger.info("codecommit.get_file response: " + str(response))
    file_content = json.loads(codecs.decode(response['fileContent']))
    print("Inside get_manifest_file()")
    return file_content

def get_asset_files(repository_name, commit_id, asset_type, asset_file_path):

    response = codecommit.get_file(repositoryName = repository_name, commitSpecifier = commit_id, filePath = asset_file_path)
    file_content = json.loads(codecs.decode(response['fileContent']))
    print("Inside get_asset_files()")
    return file_content

def create_analysis(analysis_id, analysis_name, analysis_definition_json):
    print("Inside create_analysis()")
    logger.info("Inside create_analysis()")
    try:
        response = quicksight.create_analysis(AwsAccountId =target_aws_account_id, AnalysisId = analysis_id, Name = analysis_name, Definition = analysis_definition_json)
        print("Creation status: " + response['CreationStatus'] + " ARN:" + response['Arn'])
        logger.info("Creation status: " + response['CreationStatus'] + " ARN:" + response['Arn'])
    except Exception as e:
        raise e

def update_analysis(analysis_id, analysis_name, analysis_definition_json):
    print('Inside update_analysis()')
    logger.info('Inside update_analysis()')
    try:
        response = quicksight.update_analysis(AwsAccountId =target_aws_account_id, AnalysisId = analysis_id, Name = analysis_name, Definition = analysis_definition_json)
        print('Update status: ' + response['UpdateStatus'] + ' ARN:' + response['Arn'])
        logger.info('Update status: ' + response['UpdateStatus'] + ' ARN:' + response['Arn'])
    except Exception as e:
        raise e
        
def update_analysis_permission(analysis_id, analysis_permission_json):
    print('Inside update_analysis_permission()')
    logger.info('Inside update_analysis_permission()')
    try:
        grant_permission_json = analysis_permission_json['GrantPermissions']
        time.sleep(3)
        response = quicksight.update_analysis_permissions(AwsAccountId =target_aws_account_id, AnalysisId = analysis_id, GrantPermissions = grant_permission_json)
        print('Update permission HTTP status: ' + str(response['Status']) + ' Analysis ARN:' + response['AnalysisArn'])
        logger.info('Update permission HTTP status: ' + str(response['Status']) + ' Analysis ARN:' + response['AnalysisArn'])
    except KeyError:
        revoke_permission_json = analysis_permission_json['RevokePermissions']
        #Sleep for 3 seconds in case the analysis creation/ update in progress
        response = quicksight.update_analysis_permissions(AwsAccountId =target_aws_account_id, AnalysisId = analysis_id, RevokePermissions = revoke_permission_json)
        print('Update permission HTTP status: ' + str(response['Status']) + ' Analysis ARN:' + response['AnalysisArn'])
        logger.info('Update permission HTTP status: ' + str(response['Status']) + ' Analysis ARN:' + response['AnalysisArn'])
        
def deploy_analysis(analyses_manifest):
    #Assume role that has permissions on QuickSight
    global quicksight
    sts = boto3.client('sts')
    assumedRole = sts.assume_role(
        RoleArn = roleArn,
        RoleSessionName = sessionName
        )
    stage = 'Assumed role'
        
    #Create boto3 session
    assumedRoleSession = boto3.Session(
        aws_access_key_id = assumedRole['Credentials']['AccessKeyId'],
        aws_secret_access_key = assumedRole['Credentials']['SecretAccessKey'],
        aws_session_token = assumedRole['Credentials']['SessionToken'],
    )
        
    print("Assumed role as {} ".format(roleArn))
    logger.info("Assumed role as {} ".format(roleArn))
        
    #quicksight = assumedRoleSession.client('quicksight',region_name= dashboardRegion)
    quicksight = assumedRoleSession.client('quicksight')
    stage = 'Created QuickSight client'
        
    print("quickSight Client created successfully")
    logger.info("quickSight Client created successfully")
                
    for analysis in analyses_manifest:
        analysis_id = analysis['id']
        analysis_name = analysis['name']
        analysis_filename = analysis['filename']

        analysis_definition_json = json.loads(zipfile.read(repo_analysis_path + analysis_filename))
        
        try:
            #Look for analysis definition or analysis permission definition. KeyError is raised if Key = DataSetIdentifierDeclarations not found in the json
            dummy_val = analysis_definition_json['DataSetIdentifierDeclarations']
            print("Deploying analysis... \n analysis_id: " + analysis_id + "\n analysis_name: " + analysis_name)
            logger.info("Deploying analysis... analysis_id: {}. analysis_name: {}".format(analysis_id, analysis_name))
            try:
                create_analysis(analysis_id, analysis_name, analysis_definition_json)
                print('Check analysis_id {} creation status by describe-analysis command'.format(analysis_id))
                logger.info('Check analysis_id {} creation status by describe-analysis command'.format(analysis_id))
            except excep.ClientError as e:
                if e.response['Error']['Code'] == 'ResourceExistsException':
                    print("The analysis already exist. Attempting to update the analysis ...")
                    logger.info("The analysis already exist. Attempting to update the analysis ...")
                    try:
                        update_analysis(analysis_id, analysis_name, analysis_definition_json)
                        print('Check analysis_id {} update status by describe-analysis command'.format(analysis_id))
                        logger.info('Check analysis_id {} update status by describe-analysis command'.format(analysis_id))
                    except excep.ClientError as e:
                        print('Update analysis failed due to {}'.format(e.response['Error']['Message']))
                        logger.info('Update analysis failed due to {}'.format(e.response['Error']['Message']))
                        raise e
                else:
                    raise e
        except KeyError:
            try:
                analysis_permission_json = analysis_definition_json
                update_analysis_permission(analysis_id, analysis_permission_json)
                print('Check analysis_id {} permission status by describe-analysis-permission command'.format(analysis_id))
                logger.info('Check analysis_id {} permission status by describe-analysis-permission command'.format(analysis_id))
            except excep.ClientError as e:
                print('Update analysis permission failed due to {}'.format(e.response['Error']['Message']))
                logger.info('Update analysis permission failed due to {}'.format(e.response['Error']['Message']))
                raise e
        
        
def execute_deploy():
    manifest = json.loads(zipfile.read(deployment_config_path))
    deploy_analysis(manifest['analyses'])
    #deploy_dashboard(manifest)
    #deploy_datasource(manifest)
    #deploy_theme(manifest)

def lambda_handler(event, context):
    logger.info(event)
    global zipfile
    global target_aws_account_id
    global roleArn
    
    params = json.loads(event['CodePipeline.job']['data']['actionConfiguration']['configuration']['UserParameters'])
    for param in params:
        logger.info('Userparameter: {}'.format(param))
        print('Userparameter: {}'.format(param))
        if param['name'] == 'BranchName':
            branchname = param['value'] 
        if param['name'] == 'Commit_ID':
            commit_id = param['value'] 
    
    print('BranchName: {}. Commit ID: {}'.format(branchname,commit_id))
    logger.info('BranchName: {}. Commit ID: {}'.format(branchname,commit_id))
    
    if branchname == 'master':
        target_aws_account_id = os.environ['AWS_ACCOUNT_ID_PROD']
        roleArn = os.environ['ASSUME_ROLE_ARN_PROD']
    else:
        target_aws_account_id = os.environ['AWS_ACCOUNT_ID_BETA']
        roleArn = os.environ['ASSUME_ROLE_ARN_BETA']
        
    print('Deploying will start in target AWS_ACCOUNT_ID {}'.format(target_aws_account_id))
    logger.info('Deploying will start in target AWS_ACCOUNT_ID {}'.format(target_aws_account_id))

    pipeline_id = event['CodePipeline.job']['id']
    artifact_bucket = event['CodePipeline.job']['data']['inputArtifacts'][0]['location']['s3Location']['bucketName']
    artifact_object = event['CodePipeline.job']['data']['inputArtifacts'][0]['location']['s3Location']['objectKey']
    
    print('S3 bucket: {}'.format(artifact_bucket))
    print('S3 object: {}'.format( artifact_object))
    
    bucket = s3.Bucket(artifact_bucket)
    obj = bucket.Object(artifact_object)
    
    with io.BytesIO(obj.get()["Body"].read()) as tf:
        tf.seek(0)
        
        with ZipFile(tf, mode='r') as zipfile:
            json_data = json.loads(zipfile.read(deployment_config_path))
            print(json_data)
            logger.info(json_data)
            
            try:
                print(boto3.__version__) 
                print(botocore.__version__) 
                execute_deploy()
            except Exception as e:
                print(e)
                logger.info(e)
                print('Invalid operation requested for the pipeline Id {}'.format(pipeline_id))
                logger.info('Invalid operation requested for the pipeline Id {}'.format(pipeline_id))
                #raise
    
    response = pipeline.put_job_success_result(
        jobId=event['CodePipeline.job']['id']
    )
    return response
