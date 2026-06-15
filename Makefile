# Variables - easier to change in one place
IMAGE_NAME=book-scraper
ENV_NAME=dev
REGISTRY=localhost:4566
FULL_IMAGE_URI=$(REGISTRY)/$(IMAGE_NAME):$(ENV_NAME)

.PHONY: build-lambda push-lambda deploy all docker/run docker/test

# 1. Build only the Lambda stage of the Dockerfile
build-lambda:
	docker build --target lambda_runtime -t $(FULL_IMAGE_URI) .

# 2. Run the container directly from the image WITHOUT building
docker/start-container:
	# Runs the existing local image instantly
	docker run -d --rm \
		-e PYTHONUNBUFFERED=1 \
		-p 9000:8080 \
		$(FULL_IMAGE_URI)

# 3. Run Terraform
tf-apply:
	terraform apply -auto-approve

# Run a test against the Floci ecosystem container
test/floci:
	AWS_ACCESS_KEY_ID=mock \
	AWS_SECRET_ACCESS_KEY=mock \
	aws lambda invoke \
		--endpoint-url http://floci:4566 \
		--region us-east-1 \
		--function-name $(IMAGE_NAME)-$(ENV_NAME) \
		--payload '{"sellers": ["jnts0710"]}' \
		--cli-binary-format raw-in-base64-out \
		/dev/stdout

# The "Do Everything" command
all: build-lambda push-lambda tf-apply

docker/run :
	# Creates a local screenshots directory if it doesn't exist
	mkdir -p $(PWD)/screenshots
	mkdir -p $(PWD)/debug_data

	# This runs the container locally for debugging (outside of Lambda)
	docker run --rm \
		-e PYTHONUNBUFFERED=1 \
		-p 9001:8080 \
		-v $(PWD)/screenshots:/app/screenshots \
		-v $(PWD)/debug_data:/var/task/debug \
		$(FULL_IMAGE_URI)

docker/test :
	curl -XPOST 'http://localhost:9001/2015-03-31/functions/function/invocations' -d '{"sellers": ["jnts0710", "beyond_llc_jp01", "ninja_japan_shop", "yoshihiroshop", "nkkt10-26"] }'
