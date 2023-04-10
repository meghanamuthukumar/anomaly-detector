import time
from datetime import datetime, timezone
from azure.ai.anomalydetector import AnomalyDetectorClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.anomalydetector.models import *
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler


ANOMALY_DETECTOR_ENDPOINT = "[ANOMALY_DETECTOR_ENDPOINT]"
SUBSCRIPTION_KEY = "[SUBSCRIPTION_KEY]"

ad_client = AnomalyDetectorClient(ANOMALY_DETECTOR_ENDPOINT, AzureKeyCredential(SUBSCRIPTION_KEY))

time_format = "%Y-%m-%dT%H:%M:%SZ"

train_body = ModelInfo(
        # The data source should be the Blob URL, something like: https://mvaddataset.blob.core.windows.net/sample-multitable/sample_data_5_3000.csv
        data_source="https://anomaly5164.blob.core.windows.net/elg5164/insurance-edited-version1.csv",
        # start_time and end_time are optional. If you don't set them, the whole data will be used to train the model.
        start_time="2021-01-01T00:00:00Z",
        end_time="2021-01-02T09:00:00Z",
        # If your data is one CSV file, please set the dataSchema as `OneTable`, if your data is multiple CSV files in a folder, please set the dataSchema as `MultiTable`.
        data_schema="OneTable",
        # Use display_name to name your model.
        display_name="sample",
        # Sliding window size is optional. If you don't set it, the default value is 200.
        sliding_window=200,
        # align_policy is optional. If you don't set it, the default value is `AlignPolicy(align_mode=AlignMode.OUTER, fill_n_a_method=FillNAMethod.LINEAR, padding_value=0)`.
        align_policy=AlignPolicy(
            align_mode=AlignMode.OUTER,
            fill_n_a_method=FillNAMethod.LINEAR,
            padding_value=0,
        ),
    )
batch_inference_body = MultivariateBatchDetectionOptions(
        data_source="https://anomaly5164.blob.core.windows.net/elg5164/insurance-edited-version1.csv",
        # The topContributorCount specify how many contributed variables you care about in the results, from 1 to 50.
        top_contributor_count=10,
        start_time="2021-01-01T00:18:00Z",
        end_time="2021-01-01T21:50:00Z",
    )

print("Training new model...(it may take a few minutes)")
model = ad_client.train_multivariate_model(train_body)
model_id = model.model_id
print("Training model id is {}".format(model_id))
## Wait until the model is ready. It usually takes several minutes
model_status = None
model = None


while model_status != ModelStatus.READY and model_status != ModelStatus.FAILED:
    model = ad_client.get_multivariate_model(model_id)
    # print(model)
    model_status = model.model_info.status

    print("Model is {}".format(model_status))
    time.sleep(30)


if model_status == ModelStatus.READY:
    print("Done.\n")
    # Return the latest model id

# Detect anomaly in the same data source (but a different interval)
result = ad_client.detect_multivariate_batch_anomaly(model_id, batch_inference_body)
result_id = result.result_id

# Get results (may need a few seconds)
print("Get detection result...(it may take a few seconds)")
# print("batch model status = ", anomaly_results.summary.status)
detection_status = None

while detection_status != MultivariateBatchDetectionStatus.READY and detection_status != MultivariateBatchDetectionStatus.FAILED:
    anomaly_results = ad_client.get_multivariate_batch_detection_result(result_id)
    # print(anomaly_results)
    print("Detection is {}".format(anomaly_results.summary.status))
    detection_status = anomaly_results.summary.status
    time.sleep(30)
    
   
#azure logging
logger = logging.getLogger(__name__)

#manually pass in the connection_string
logger.addHandler(AzureLogHandler(connection_string="InstrumentationKey=a06ed340-b358-4634-823a-5b91beec8467;IngestionEndpoint=https://eastus2-3.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus2.livediagnostics.monitor.azure.com/"))


# See detailed inference result
for r in anomaly_results.results:
    if ( r.value.is_anomaly == True):
        print(
            "timestamp: {}, is_anomaly: {}, anomaly score: {:.4f}, severity: {:.4f}".format(
                r.timestamp,
                r.value.is_anomaly,
                r.value.score,
                r.value.severity,
            )
        )
        if r.value.interpretation:
            for contributor in r.value.interpretation:
                print(
                    "\tcontributor variable: {:<10}, contributor score: {:.4f}".format(
                        contributor.variable, contributor.contribution_score
                    )
                )
                logger.warning(f"\tAnomaly Interpretation- contributor variable: {contributor.variable}, contributor score: {contributor.contribution_score}, timestamp: {r.timestamp}")

print("Result ID:\t", anomaly_results.result_id)
print("Result status:\t", anomaly_results.summary.status)
print("Result length:\t", len(anomaly_results.results))
anomalyList = []
for r in anomaly_results.results:
    if ( r.value.is_anomaly == True):
        anomalyList.append(r)
print("Number of anomalies detected: \t", len(anomalyList))

    