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

*	The AWS Code Commit code repository must have 2 branches- master and beta.
* Amazon QuickSight asset definition file from the Beta environment should be available. For example to deploy an Amazon QuickSight analysis asset, you should know how to use the describe-analysis-definition CLI command and how to strip the output of the describe-analysis-definition command to be useful for deployment into production.
* You should consider maintaining IAM user groups to allow/ limit pushes and merges the above branches using AWS Code Commit IAM policies as described in Limit pushes and merges to branches in AWS CodeCommit.

### Deployment guide

#### AWS Code Commit

**Setup IAM user for Code Commit repository access**

Step 1: AWS IAM > Users > Search or Add users > Permissions > Add permissions > Attach policies directly > AWSCodeCommitPowerUser

![image](https://user-images.githubusercontent.com/14042866/228686337-13d87f2d-8636-4346-9fc8-6cc894e50afc.jpeg)

Step 2:  Install Git locally: to install Git, we recommend websites such as [Git Downloads](http://git-scm.com/downloads).

Step 3: AWS IAM > Users > Search or Add users > Security credentials > HTTPS Git credentials for AWS CodeCommit > Generate credentials 

![image](https://user-images.githubusercontent.com/14042866/228686620-cca0b6d7-9ac7-4e62-8166-ee006314f4e1.jpeg)

![image](https://user-images.githubusercontent.com/14042866/228686627-8933f7f4-936b-4798-9b87-a5eb973cd75d.jpeg)

**Setup AWS CodeCommit repository**

Step 1: AWS > CodeCommit > Source > Repositories > Create repository

![image](https://user-images.githubusercontent.com/14042866/228686664-07d2a112-8f71-475a-bd5f-7a8096d1f847.jpeg)

![image](https://user-images.githubusercontent.com/14042866/228686678-b59a89ee-62ba-45c8-ad8a-294ce316aeb0.jpeg)

![image](https://user-images.githubusercontent.com/14042866/228686687-56552b4c-a4db-4898-bc6b-072d8c516b80.jpeg)

Step 2: Clone repository to local

Open a terminal in your local and enter below command. Replace the repository URL with your repository in your AWS region. If you are prompted for repository password, enter the downloaded credential retrieved during setting up HTTPS Git credentials for AWS CodeCommit > Generate credentials step described in the previous step.

`
git clone https://git-codecommit.us-east-1.amazonaws.com/v1/repos/QuickSightAssets qs-asset-repo
`
![image](https://user-images.githubusercontent.com/14042866/228686930-0da4139b-40ff-4229-84cd-1bd8f50c4aad.jpeg)


Step 3: Create repository folder structure locally

Run below commands from the local repository directory created above.

`
$mkdir datasource dataset analysis dashboard theme scripts
`

`
$echo "{   
"datasources": [{}],
"datasets": [{}],
"analyses": [{}],
"dashboards": [{}],
"themes": [{}]
}" >>  scripts/deploy-config.json
`

`
$git add scripts/
`

`
$git commit -m "Initial scripts file"
`

`
$git push
`

After the final step above, come back to AWS console and navigate to your CodeCommit repository. You will see the deploy-config.json file got created.

![image](https://user-images.githubusercontent.com/14042866/228687039-3ade741f-bcc1-4af2-a655-838cbd5ace4f.jpeg)


### Testing guide

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

