import subprocess
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DigitHandler:

    @staticmethod
    def _get_device_info_from_sysfs(device_path: str) -> dict:
        """
        Tries to find the model, manufacturer, revision, and serial number for a given video device
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
            sysfs_path = os.path.realpath(f"/sys/class/video4linux/{os.path.basename(device_path)}/device")

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
            logger.error(f"Error retrieving device information for {device_path}: {e}")

        return device_info

    @staticmethod
    def _parse(device_info: dict) -> dict:
        """
        Parses the device info and includes detailed information by querying the sysfs.
        Sets dev_name to the first video device path from the paths list.
        """
        main_device_path = device_info["paths"][0] if device_info["paths"] else None
        sysfs_info = DigitHandler._get_device_info_from_sysfs(main_device_path) if main_device_path else {}

        digit_info = {
            "dev_name": main_device_path,  # Use the first available video device path as dev_name
            "paths": device_info.get("paths", []),
            "manufacturer": sysfs_info.get("manufacturer", "Unknown"),
            "model": sysfs_info.get("model", "Unknown"),
            "revision": sysfs_info.get("revision", "Unknown"),
            "serial": sysfs_info.get("serial", "Unknown")
        }
        return digit_info


    @staticmethod
    def list_digits() -> List[Dict[str, str]]:
        """
        List video devices using v4l2-ctl and filter for devices with 'DIGIT' in the name.
        """
        try:
            # Run the v4l2-ctl command to list video devices
            result = subprocess.run(['v4l2-ctl', '--list-devices'], stdout=subprocess.PIPE, text=True, check=True)
            output = result.stdout
            
            logger.debug("v4l2-ctl --list-devices output:\n" + output)

            # Parse the output to find devices with 'DIGIT' in their name or model
            devices = []
            current_device = None
            for line in output.splitlines():
                if line.strip() == "":
                    continue
                if not line.startswith("\t"):  # Device name/model line
                    current_device = {'name': line.strip(), 'paths': []}
                    if 'DIGIT' in current_device['name']:
                        devices.append(current_device)
                else:  # Device path line (indented)
                    if current_device and 'DIGIT' in current_device['name']:
                        current_device['paths'].append(line.strip())

            # Convert the devices to the format expected by the original code, including serial number
            parsed_devices = [DigitHandler._parse(device) for device in devices]

            if not parsed_devices:
                logger.debug("Could not find any devices matching 'DIGIT'")
                
            return parsed_devices
        
        except subprocess.CalledProcessError as e:
            logger.error(f"An error occurred while running v4l2-ctl: {e}")
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