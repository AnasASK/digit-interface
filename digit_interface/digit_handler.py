import subprocess
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DigitHandler:

    @staticmethod
    def _get_serial_from_sysfs(device_path: str) -> str:
        """
        Tries to find the serial number for a given video device by tracing its parent
        in the sysfs directory.
        """
        try:
            # Resolve the sysfs path of the device
            sysfs_path = os.path.realpath(f"/sys/class/video4linux/{os.path.basename(device_path)}/device")
            
            # Traverse up to find the USB device (if applicable)
            while sysfs_path:
                serial_path = os.path.join(sysfs_path, "serial")
                if os.path.exists(serial_path):
                    with open(serial_path, 'r') as serial_file:
                        return serial_file.read().strip()
                sysfs_path = os.path.dirname(sysfs_path)  # Move up one level
        except Exception as e:
            logger.error(f"Error retrieving serial number for {device_path}: {e}")
        
        return "Unknown"

    @staticmethod
    def _parse(device_info: dict) -> dict:
        """
        Parses the device info and includes the serial number by querying the sysfs.
        Sets dev_name to the first video device path from the paths list.
        """
        # We will assume the first path in the paths list is the main device path
        main_device_path = device_info["paths"][0] if device_info["paths"] else None
        serial_number = DigitHandler._get_serial_from_sysfs(main_device_path) if main_device_path else "Unknown"
        
        digit_info = {
            "dev_name": main_device_path,  # Use the first available video device path as dev_name
            "paths": device_info.get("paths", []),
            "manufacturer": "Unknown",  # Could be retrieved with further sysfs parsing if needed
            "model": device_info.get("name", "Unknown"),
            "revision": "2021",  # Could also be retrieved from sysfs in a similar manner
            "serial": serial_number
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


# Example usage:
if __name__ == "__main__":
    digit_devices = DigitHandler.list_digits()
    for device in digit_devices:
        print(device)
    
    # Find a specific device by serial
    serial_to_find = "123456789ABC"
    found_device = DigitHandler.find_digit(serial_to_find)
    if found_device:
        print(f"Found device: {found_device}")
    else:
        print(f"No device with serial {serial_to_find} found")
