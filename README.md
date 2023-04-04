## Amazon QuickSight Asset Migration CI/ CD

This is a prescriptive guidance to implement code integration and code deployment (CI/ CD) pipeline for migrating Amazon QuickSight assets from less restrictive environment such as Beta to a more restrictive environment such as Production.  

### Architecture

<img width="468" alt="image" src="https://user-images.githubusercontent.com/14042866/228686061-325c3978-ff86-4559-9b53-32ef54defc04.png">

The architecture uses the below AWS services.

1.	AWS Code Commit
2.	AWS Lambda
3.	Amazon QuickSight
4.	Amazon Identity and Access Management (IAM)
5.	Amazon S3
6.	AWS Code Pipeline

### Pre-requisite

*	The AWS Code Commit code repository must have 2 branches- **_master_** and **_beta_**.

* Amazon QuickSight asset definition file from the Beta environment should be available. For example to deploy an Amazon QuickSight analysis asset, you should know how to use the [**describe-analysis-definition**](https://docs.aws.amazon.com/cli/latest/reference/quicksight/describe-analysis-definition.html) CLI command and how to modify the output of the describe-analysis-definition command to use as input to [**create-analysis**](https://docs.aws.amazon.com/cli/latest/reference/quicksight/create-analysis.html) CLI command.

* You should consider maintaining IAM user groups to allow/ limit Git push and merg the above branches using AWS Code Commit IAM policies as described in [Limit pushes and merges to branches in AWS CodeCommit](https://docs.aws.amazon.com/codecommit/latest/userguide/how-to-conditional-branch.html).

### Deployment guide

#### 1. AWS Code Commit

**_Setup IAM user who will access the AWS Code Commit repository_**

Step 1: **AWS IAM > Users > Search or Add users > Permissions > Add permissions > Attach policies directly > AWSCodeCommitPowerUser**

![image](https://user-images.githubusercontent.com/14042866/228686337-13d87f2d-8636-4346-9fc8-6cc894e50afc.jpeg)

Step 2:  Install Git locally: to install Git, we recommend websites such as [Git Downloads](http://git-scm.com/downloads).

Step 3: **AWS IAM > Users > Search or Add users > Security credentials > HTTPS Git credentials for AWS CodeCommit > Generate credentials **

![image](https://user-images.githubusercontent.com/14042866/228686620-cca0b6d7-9ac7-4e62-8166-ee006314f4e1.jpeg)

![image](https://user-images.githubusercontent.com/14042866/228686627-8933f7f4-936b-4798-9b87-a5eb973cd75d.jpeg)

**_Setup the AWS CodeCommit repository_**

Step 1: **AWS > CodeCommit > Source > Repositories > Create repository**

![image](https://user-images.githubusercontent.com/14042866/228686664-07d2a112-8f71-475a-bd5f-7a8096d1f847.jpeg)

![image](https://user-images.githubusercontent.com/14042866/228686678-b59a89ee-62ba-45c8-ad8a-294ce316aeb0.jpeg)

![image](https://user-images.githubusercontent.com/14042866/228686687-56552b4c-a4db-4898-bc6b-072d8c516b80.jpeg)

Step 2: Clone repository to local

Open a terminal in your local and enter below command. Replace the repository URL with your repository in your AWS region. If you are prompted for repository password, enter the downloaded credential retrieved during setting up HTTPS Git credentials for _AWS CodeCommit > Generate credentials_ step described in the previous step.

`
git clone https://git-codecommit.us-east-1.amazonaws.com/v1/repos/QuickSightAssets qs-asset-repo
`
![image](https://user-images.githubusercontent.com/14042866/228686930-0da4139b-40ff-4229-84cd-1bd8f50c4aad.jpeg)


Step 3: Create repository folder structure in local repository

Run below commands from the terminal inside the local repository directory created above.

```
$mkdir datasource dataset analysis dashboard theme scripts

$echo "{   
"datasources": [{}],
"datasets": [{}],
"analyses": [{}],
"dashboards": [{}],
"themes": [{}]
}" >>  scripts/deploy-config.json

$git add scripts/

$git commit -m "Initial scripts file"

$git push
```

After the final step above, come back to AWS console and navigate to your AWS CodeCommit repository. You will see the _deploy-config.json_ file got created.

![image](https://user-images.githubusercontent.com/14042866/228687039-3ade741f-bcc1-4af2-a655-838cbd5ace4f.jpeg)

#### 2. AWS IAM

**_Configurations in the source AWS account_**

In the Beta account i.e where the CI/ CD Code Pipeline is being setup, create below IAM roles

1. _**Current-Account-QuickSight-Asset-CRUD**_

![image](https://user-images.githubusercontent.com/14042866/229652988-0a8e8146-4d03-447e-928a-7f69c87f03cf.jpeg)

_Trust relationship_

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::<source-account-id>:root"
            },
            "Action": "sts:AssumeRole",
            "Condition": {}
        }
    ]
}
```

_Inline Policy (**Quicksight-assets-create-update**)_

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "quicksight:CreateDashboard",
                "quicksight:PassDataSet",
                "quicksight:CreateDataSet",
                "quicksight:UpdateDataSet",
                "quicksight:UpdateThemePermissions",
                "quicksight:CreateDataSource",
                "quicksight:UpdateDataSource",
                "quicksight:CreateTheme",
                "quicksight:UpdateDataSetPermissions",
                "quicksight:CreateAnalysis",
                "quicksight:UpdateDataSourcePermissions",
                "quicksight:UpdateAnalysisPermissions",
                "quicksight:UpdateDashboardPermissions",
                "quicksight:UpdateDashboard",
                "quicksight:UpdateAnalysis",
                "quicksight:UpdateTheme"
            ],
            "Resource": "*"
        }
    ]
}
```

2.	_**quicksight-assets-pipeline1-role**_

![image](https://user-images.githubusercontent.com/14042866/229653575-7d539032-400c-485d-b18b-a69ec10aec70.jpeg)

![image](https://user-images.githubusercontent.com/14042866/229653584-ff2b4578-1007-4370-bfc7-8c168c6b2fa2.jpeg)

_Trust relationship_

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

_Inline Policies_

1. _CodePipeline-PutJobSuccessfulResult_

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": "codepipeline:PutJobSuccessResult",
            "Resource": "*"
        }
    ]
}
```

2. _STSAssumeRolePolicy_

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AssumeRole",
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": [
                "arn:aws:iam::<target-account-id>:role/Cross-Account-QuickSight-Asset-CRUD",
                "arn:aws:iam::<source-account-id>:role/Current-Account-QuickSight-Asset-CRUD"
            ]
        }
    ]
}
```

**_Configurations in the target AWS account_**

In the target AWS account i.e where the CI/ CD Code Pipeline will deploy the Amazon QuickSight assets, create the below IAM role

_**Cross-Account-QuickSight-Asset-CRUD**_

![image](https://user-images.githubusercontent.com/14042866/229653838-96d8acb0-0b05-4efb-9fa9-114230fd9642.jpeg)

_Trust relationship_

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::<source-account-id>:role/service-role/quicksight-assets-pipeline1-role "
            },
            "Action": "sts:AssumeRole",
            "Condition": {}
        }
    ]
}
```

_Inline Policy (**_Quicksight-assets-create-update_**)_

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "quicksight:CreateDashboard",
                "quicksight:PassDataSet",
                "quicksight:CreateDataSet",
                "quicksight:UpdateDataSet",
                "quicksight:UpdateThemePermissions",
                "quicksight:CreateDataSource",
                "quicksight:UpdateDataSource",
                "quicksight:CreateTheme",
                "quicksight:UpdateDataSetPermissions",
                "quicksight:CreateAnalysis",
                "quicksight:UpdateDataSourcePermissions",
                "quicksight:UpdateAnalysisPermissions",
                "quicksight:UpdateDashboardPermissions",
                "quicksight:UpdateDashboard",
                "quicksight:UpdateAnalysis",
                "quicksight:UpdateTheme"
            ],
            "Resource": "*"
        }
    ]
}
```

#### 3. AWS Lambda

Step 1: Create a Lambda function _quicksight-assets-pipeline_ from scratch with Runtime **Python 3.8**, select Execution role as **Use an existing role**

![image](https://user-images.githubusercontent.com/14042866/229653988-53cbe1ad-59ca-40ec-b075-cc44e9c8f2ab.jpeg)

Step 2: Update Lambda configuration

1. Change the timeout to 30 seconds

![image](https://user-images.githubusercontent.com/14042866/229659830-655bfd10-76c0-405b-be16-4e13efb4a32e.jpeg)


2.  Add the below 4 environment variables
* ASSUME_ROLE_ARN_BETA --> arn:aws:iam::<source-aws-account-id>:role/Cross-Account-QuickSight-Asset-CRUD
* ASSUME_ROLE_ARN_PROD	--> arn:aws:iam::<target-aws-account-id>:role/Current-Account-QuickSight-Asset-CRUD
* AWS_ACCOUNT_ID_BETA --> <source-aws-account-id>
* AWS_ACCOUNT_ID_PROD --> <target-aws-account-id>
  
![image](https://user-images.githubusercontent.com/14042866/229659841-3c5574ea-1f46-4dd6-a9ce-b754c316d4f9.jpeg)

Step 3: Add the below code to the Lambda function.

Download the code from https://aws-psa-analytics.s3.amazonaws.com/quicksight/deploy-qs-assets_s3source.py and paste into the AWS Lambda function lambda_function.py editor.

Step 4: Navigate to **Configuration** tab. Under Execution role you will see a role name prefixed as _quicksight-assets-pipeline-role_ got created. Click on this role to open the IAM console. We will attach appropriate policies to this role here for the lambda function to perform actions on Amazon QuickSight and AWS Code Pipeline.

![image](https://user-images.githubusercontent.com/14042866/229654155-056f47f4-24fd-445b-a7c3-8d1ae82ebea7.jpeg)

Step 5: Check for below policies are attached to the _quicksight-assets-pipeline-role-<xxxxxxxx>_ IAM role.

*	AWSLambdaBasicExecutionRole
*	AmazonS3FullAccess
*	CodePipeline-PutJobSuccessfulResult
*	STSAssumeRolePolicy

Step 6: Attach latest boto3 lambda layer

Follow the steps described [here](https://aws.amazon.com/premiumsupport/knowledge-center/lambda-python-runtime-errors/) to attach the latest boto3 lambda layer.

![image](https://user-images.githubusercontent.com/14042866/229654280-6392d824-7c0e-47ef-bce7-98de69c6be83.jpeg)
  

#### 4. AWS Code Pipeline
  
Step 1: Create Pipeline
  
![image](https://user-images.githubusercontent.com/14042866/229655013-54140d0a-5e1a-4874-8582-0564973c5448.jpeg)

![image](https://user-images.githubusercontent.com/14042866/229655032-b1d79077-51c6-42bb-85da-a5c191803194.jpeg)

![image](https://user-images.githubusercontent.com/14042866/229655051-e3d3ad34-1a1d-409d-a263-56121d2346e0.jpeg)

![image](https://user-images.githubusercontent.com/14042866/229655082-8d350f71-33b7-43db-9f21-fb7d5e000638.jpeg)

![image](https://user-images.githubusercontent.com/14042866/229655101-f4b83eb5-03c5-49cf-a76d-07b4eaca48fc.jpeg)
  
![image](https://user-images.githubusercontent.com/14042866/229655110-1dec01e3-75c3-485d-8bab-74fd6f9b7296.jpeg)
  
Step 2: Edit Pipeline “Deploy” stage
  
![image](https://user-images.githubusercontent.com/14042866/229655157-3aece356-e966-4081-9567-0d7dc4c028bb.jpeg)
  
![image](https://user-images.githubusercontent.com/14042866/229655171-99fe2aa2-bd27-4995-be48-16af31b40d0e.jpeg)
  
_User parameters_
  
```
  [{"name":"BranchName","value":"#{SourceVariables.BranchName}","type":"PLAINTEXT"},{"name":"Commit_ID","value":"#{SourceVariables.CommitId}","type":"PLAINTEXT"}]
 ```
  
![image](https://user-images.githubusercontent.com/14042866/229655232-e46d7f25-c888-4d35-96e3-0ec7d76e736b.jpeg)

### Testing guide
  
Step 1: Download one of the analysis definition from the source AWS account by running [describe-analysis-definition](https://docs.aws.amazon.com/cli/latest/reference/quicksight/describe-analysis-definition.html#describe-analysis-definition) API.
  
Step 2: Update the downloaded JSON file to be used as input to QuickSight [create-analysis](https://docs.aws.amazon.com/cli/latest/reference/quicksight/create-analysis.html) API. If you save this file as **analysis-definition-to-migrate.json**
  
Step 3: Move the modified JSON file under the analysis folder of your local repository
  
Step 4: Modify the scripts/deploy-config.json file as below
  
```
{
"datasources": [{}],
"datasets": [{}],
"analyses": [{"id":"some-alphanumeric-id-you-want", "name": "Some Name You Want to Call", "filename": "analysis-definition-to-migrate.json"}],
"dashboards": [{}],
"themes": [{}]
}
```
  
Step 5: Execute the below commands from terminal
  
```
$  git status 
$  git add deploy-config.json ../analysis/
$ git commit -m "New analysi ssome-alphanumeric-id-you-want definition added"
$ git push

  ```
  
![image](https://user-images.githubusercontent.com/14042866/229657392-09d3d686-8f60-43e9-9c1e-5878fcd4ddce.jpeg)
  
![image](https://user-images.githubusercontent.com/14042866/229657406-6416bec1-639c-444b-9802-076ed4be0432.jpeg)

  
Step 6: Navigate to AWS Code Pipeline console 
  
![image](https://user-images.githubusercontent.com/14042866/229657644-960422a5-5d6a-44d3-bb95-babba711490c.jpeg)
  
![image](https://user-images.githubusercontent.com/14042866/229657679-aa124229-f2db-4103-830d-8b0cb0240f7d.jpeg)


Step 7: Check the AWS CloudWatch log
  
![image](https://user-images.githubusercontent.com/14042866/229657763-454ca040-faeb-438e-b89c-cf06e482480f.jpeg)

![image](https://user-images.githubusercontent.com/14042866/229657771-69d25ee3-9010-4ff5-b4b6-77abc2be4ae5.jpeg)

  
## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

