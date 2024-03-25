import json
from typing import Optional, Dict, Any, List

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build

from gitops_utils.utils import Utils, get_cloud_call_params


def get_google_call_params(max_results: Optional[int] = 200, **kwargs):
    return get_cloud_call_params(
        max_results=max_results, first_letter_to_lower=True, **kwargs
    )


class GoogleClient(Utils):
    def __init__(
        self,
        scopes: List[str],
        subject: str,
        service_account_file: Optional[str | Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.SCOPES = scopes
        self.SUBJECT = subject

        if service_account_file is None:
            self.GOOGLE_SERVICE_ACCOUNT = self.decode_input(
                "GOOGLE_SERVICE_ACCOUNT", required=True
            )
        elif isinstance(service_account_file, str):
            self.GOOGLE_SERVICE_ACCOUNT = json.loads(service_account_file)
        else:
            self.GOOGLE_SERVICE_ACCOUNT = service_account_file

        self.credentials = None
        self.refresh_credentials()
        self.services = {}

    def refresh_credentials(self):
        if not self.credentials or not self.credentials.valid:
            if (
                self.credentials
                and self.credentials.expired
                and self.credentials.refresh_token
            ):
                self.logger.info("Attempting to refreshing Google authentication")
                self.credentials.refresh(Request())
            else:
                google_service_account = json.loads(self.GOOGLE_SERVICE_ACCOUNT)
                self.credentials = (
                    service_account.Credentials.from_service_account_info(
                        google_service_account, scopes=self.SCOPES, subject=self.SUBJECT
                    )
                )

        return self.credentials

    def get_service(self, service_name: str, version_name: str):
        if service_name not in self.services:
            self.services[service_name] = {}

        versions = self.services[service_name]

        version = versions.get(version_name)
        if not version:
            version = build(
                serviceName=service_name,
                version=version_name,
                credentials=self.credentials,
            )
            versions[version_name] = version
            self.services[service_name] = versions

        return version
