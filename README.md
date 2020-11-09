# AWS S3 to ES import logs ELB and Cloudfront

Lambda function that import logs from ELB and Cloudfront, saved them previously into a bucket S3, to ElasticSearch Service.

## Use

1. Zip the file aws_parse_logs.py.

```bash

zip your_script_zip_name.zip aws_parse_logs.py

```
2. Install the requirements to launch correctly the function. **Path is necessary**.

```bash

pip3 install -r requirements.txt -t python/lib/python3.8/site-packages/

```
3. Zip the folder with contains every libraries.

```bash

zip -r your_layer_zip_name.zip python

```

4. Create the layer, uploading the zip generated previously.

5. Create the lambda function, upload the zip generate previously.

You need to setup this options:

### Global Environments

- **logtype**: type of log where we need parsed and import into ElasticSearch. The values must be **LoadBalancer** or **CloudFront**.
- **endpoint**: the url of your ElasticSearch Service.
- **region**: region where we created our ElasticSearch Service. Need it to AWS credentials request.
- **logindex**: prefix for your index name. Example: *myindex-<YYYY.MM.DD>*

### Notifications

Setup the notification from S3, with ObjectCreated event type.

### Basic setup

- Change the name for the controller to **aws_parse_logs.main**.
- Change timeout to 60 or upper, depends your needs.

### Permissions and role

Make sure that your role have access to bucket S3, Cloudwatch for logging the launch and ES Service, and your lambda function has the permissions to launch the function.

6. Deploy, break and fun!
