## Amazon Rekognition Twitter Selfie 

In this Serverless app we show a rank of the happiest, saddest among other emotions   [Amazon Rekoginition]([Amazon Rekognition – Video and Image - AWS](https://aws.amazon.com/rekognition/)  can detect of twits that have the word selfie in it. The app relies on lambda functions that extract, process, store and report the information from the picture. It is important to note that Twitter is a public platform that does not moderate photos uploaded by its users. This demo uses the AWS Reckognition moderation feature, but from occasionally inappropriate photos can appear. **User at your own discretion**

See the diagram below for a depiction of the complete architecture.

<img src="images/twitter-selfie.png" alt="architecture" width="1400"/>

## Initial environment setup

### Prerequisites

The Twitter-Selfie app is deployed through CloudFormation with an additional Vue.js application configuration. The following resources are required to be installed:

- [cfn-cli](https://github.com/Kotaimen/awscfncli) - A tool to abstract and simplify CloudFormation stack deployments
- npm to be able to build the Vue.js app
- [aws cli](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html) to be able to interact with the AWS resources

### Step 1: Execute cnf-cli to deploy all resources

1. clone this repo and go to its directory
2. Execute cnf-cli to deploy all resources based on the *cfn-cli.yaml* file.
```
cfn-cli stack deploy
```

### Step 2: Install and integrate the AWS Serverless twitter event source

1. Deploy the https://github.com/awslabs/aws-serverless-twitter-event-source at the same account and region you have deploy the resources on the previous step. 
2. For the App Parameters use: 
   - **SearchText** - *selfie* 
   - **StreamModeEnabled** - *true*
   - **BatchSize** - 15
   - **TweetProcessorFunctionName** - The Parser's Lambda Function Arn. The StackName by default is **twitterSelfie**
     - To obtain the Parser Function Arn you can execute
  ```
  aws cloudformation describe-stack-resource --stack-name <stackname>-lambdas --logical-resource-id Parser --query "StackResourceDetail.PhysicalResourceId"
  
  aws lambda get-function --function-name <LambdaName from step above> --query "Configuration.FunctionArn"
  ```

### Step 3: Deploy Vue.js app into S3

