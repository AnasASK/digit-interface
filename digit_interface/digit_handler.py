import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class DigitHandler:

    @staticmethod
    def _get_device_info_from_sysfs(device_name: str) -> dict:
        """
        Retrieves the model, manufacturer, revision, and serial number for a given video device
        by querying the sysfs directory.
        """
        device_info = {
            "serial": "Unknown",
            "manufacturer": "Unknown",
            "model": "Unknown",
            "revision": "Unknown"
        }

        try:
            # Resolve the sysfs path of the device
            sysfs_path = os.path.realpath(f"/sys/class/video4linux/{device_name}/device")

            # Get Serial Number
            serial_path = os.path.join(sysfs_path, "../serial")
            if os.path.exists(serial_path):
                with open(serial_path, 'r') as serial_file:
                    device_info["serial"] = serial_file.read().strip()

            # Get Manufacturer
            manufacturer_path = os.path.join(sysfs_path, "../manufacturer")
            if os.path.exists(manufacturer_path):
                with open(manufacturer_path, 'r') as manufacturer_file:
                    device_info["manufacturer"] = manufacturer_file.read().strip()

            # Get Model
            model_path = os.path.join(sysfs_path, "../product")
            if os.path.exists(model_path):
                with open(model_path, 'r') as model_file:
                    device_info["model"] = model_file.read().strip()

            # Get Revision
            revision_path = os.path.join(sysfs_path, "../bcdDevice")
            if os.path.exists(revision_path):
                with open(revision_path, 'r') as revision_file:
                    device_info["revision"] = revision_file.read().strip()

        except Exception as e:
            logger.error(f"Error retrieving device information for {device_name}: {e}")

        return device_info

    @staticmethod
    def _parse(device_name: str) -> dict:
        """
        Parses the device info and includes detailed information by querying the sysfs.
        """
        sysfs_info = DigitHandler._get_device_info_from_sysfs(device_name)

        digit_info = {
            "dev_name": f"/dev/{device_name}",  # The video device path
            "manufacturer": sysfs_info.get("manufacturer", "Unknown"),
            "model": sysfs_info.get("model", "Unknown"),
            "revision": sysfs_info.get("revision", "Unknown"),
            "serial": sysfs_info.get("serial", "Unknown")
        }
        return digit_info

    @staticmethod
    def list_digits() -> List[Dict[str, str]]:
        """
        Lists video devices by scanning the /dev directory and filtering for devices with 'DIGIT' in their name.
        """
        video_devices_path = "/dev"
        devices = []
        
        try:
            # List all video devices from the /dev directory
            for device_name in os.listdir(video_devices_path):
                if device_name.startswith("video"):
                    device_info = DigitHandler._parse(device_name)
                    if 'DIGIT' in device_info['model']:
                        devices.append(device_info)

            if not devices:
                logger.debug("Could not find any devices matching 'DIGIT'")

            return devices

        except Exception as e:
            logger.error(f"An error occurred while listing video devices: {e}")
            return []

    @staticmethod
    def find_digit(serial: str) -> Optional[Dict[str, str]]:
        """
        Finds a specific DIGIT device by its serial number.
        """
        digits = DigitHandler.list_digits()
        logger.debug(f"Searching for DIGIT with serial number {serial}")
        for digit in digits:
            if digit["serial"] == serial:
                return digit
        logger.error(f"No DIGIT with serial number {serial} found")
        return None
