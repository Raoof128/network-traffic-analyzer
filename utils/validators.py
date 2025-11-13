"""
Input Validation Module
Comprehensive validation for command-line arguments and user inputs
"""

import os
import re
from pathlib import Path
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class InputValidator:
    """Validate user inputs and command-line arguments"""

    @staticmethod
    def validate_file_exists(file_path: str, file_type: str = "file") -> Path:
        """
        Validate that a file exists and is readable

        Args:
            file_path: Path to the file
            file_type: Type of file for error messages

        Returns:
            Validated Path object

        Raises:
            ValidationError: If file doesn't exist or isn't readable
        """
        if not file_path:
            raise ValidationError(f"{file_type} path cannot be empty")

        path = Path(file_path)

        if not path.exists():
            raise ValidationError(f"{file_type} not found: {file_path}")

        if not path.is_file():
            raise ValidationError(f"Path is not a file: {file_path}")

        if not os.access(path, os.R_OK):
            raise ValidationError(f"{file_type} is not readable: {file_path}")

        return path

    @staticmethod
    def validate_file_extension(file_path: str, allowed_extensions: List[str]) -> Path:
        """
        Validate file extension

        Args:
            file_path: Path to the file
            allowed_extensions: List of allowed extensions (e.g., ['.pcap', '.pcapng'])

        Returns:
            Validated Path object

        Raises:
            ValidationError: If extension is not allowed
        """
        path = Path(file_path)

        if path.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
            raise ValidationError(
                f"Invalid file extension. Expected one of {allowed_extensions}, "
                f"got '{path.suffix}' for file: {file_path}"
            )

        return path

    @staticmethod
    def validate_output_path(output_path: str, create_dirs: bool = True) -> Path:
        """
        Validate output path and optionally create parent directories

        Args:
            output_path: Path to output file
            create_dirs: Whether to create parent directories

        Returns:
            Validated Path object

        Raises:
            ValidationError: If path is invalid
        """
        if not output_path:
            raise ValidationError("Output path cannot be empty")

        path = Path(output_path)

        # Check if parent directory exists or can be created
        parent = path.parent
        if not parent.exists():
            if create_dirs:
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created output directory: {parent}")
                except OSError as e:
                    raise ValidationError(f"Cannot create output directory {parent}: {e}")
            else:
                raise ValidationError(f"Output directory does not exist: {parent}")

        # Check if we can write to the parent directory
        if not os.access(parent, os.W_OK):
            raise ValidationError(f"Output directory is not writable: {parent}")

        # Check if file already exists (warn, but don't fail)
        if path.exists() and path.is_file():
            logger.warning(f"Output file already exists and will be overwritten: {output_path}")

        return path

    @staticmethod
    def validate_pcap_file(pcap_path: str) -> Path:
        """
        Validate PCAP file

        Args:
            pcap_path: Path to PCAP file

        Returns:
            Validated Path object

        Raises:
            ValidationError: If file is invalid
        """
        # Check existence and readability
        path = InputValidator.validate_file_exists(pcap_path, "PCAP file")

        # Check extension
        InputValidator.validate_file_extension(
            pcap_path,
            ['.pcap', '.pcapng', '.cap']
        )

        # Check minimum file size (PCAP files have headers, so should be at least 24 bytes)
        if path.stat().st_size < 24:
            raise ValidationError(f"PCAP file appears to be empty or corrupted: {pcap_path}")

        return path

    @staticmethod
    def validate_model_file(model_path: str) -> Path:
        """
        Validate model file

        Args:
            model_path: Path to model file

        Returns:
            Validated Path object

        Raises:
            ValidationError: If file is invalid
        """
        # Check existence and readability
        path = InputValidator.validate_file_exists(model_path, "Model file")

        # Check extension
        InputValidator.validate_file_extension(model_path, ['.pkl', '.pickle', '.joblib'])

        return path

    @staticmethod
    def validate_csv_file(csv_path: str) -> Path:
        """
        Validate CSV file

        Args:
            csv_path: Path to CSV file

        Returns:
            Validated Path object

        Raises:
            ValidationError: If file is invalid
        """
        # Check existence and readability
        path = InputValidator.validate_file_exists(csv_path, "CSV file")

        # Check extension
        InputValidator.validate_file_extension(csv_path, ['.csv', '.tsv', '.txt'])

        # Check minimum file size
        if path.stat().st_size < 1:
            raise ValidationError(f"CSV file appears to be empty: {csv_path}")

        return path

    @staticmethod
    def validate_network_interface(interface: Optional[str]) -> Optional[str]:
        """
        Validate network interface name

        Args:
            interface: Network interface name

        Returns:
            Validated interface name or None

        Raises:
            ValidationError: If interface name is invalid
        """
        if interface is None:
            return None

        # Check for reasonable interface name patterns
        # Common patterns: eth0, wlan0, en0, lo, etc.
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', interface):
            raise ValidationError(
                f"Invalid interface name: {interface}. "
                "Interface names should contain only alphanumeric characters, hyphens, underscores, and dots."
            )

        if len(interface) > 16:  # Linux IFNAMSIZ is 16
            raise ValidationError(f"Interface name too long (max 16 characters): {interface}")

        return interface

    @staticmethod
    def validate_bpf_filter(bpf_filter: Optional[str]) -> Optional[str]:
        """
        Validate BPF (Berkeley Packet Filter) syntax (basic validation)

        Args:
            bpf_filter: BPF filter string

        Returns:
            Validated filter string or None

        Raises:
            ValidationError: If filter syntax is obviously invalid
        """
        if bpf_filter is None or bpf_filter.strip() == "":
            return None

        filter_str = bpf_filter.strip()

        # Basic sanity checks
        if len(filter_str) > 1000:
            raise ValidationError("BPF filter too long (max 1000 characters)")

        # Check for balanced parentheses
        if filter_str.count('(') != filter_str.count(')'):
            raise ValidationError("BPF filter has unbalanced parentheses")

        # Check for common BPF keywords (not exhaustive, just sanity check)
        valid_keywords = {
            'tcp', 'udp', 'icmp', 'ip', 'ip6', 'arp', 'rarp',
            'port', 'host', 'net', 'src', 'dst', 'and', 'or', 'not',
            'greater', 'less', 'proto', 'portrange'
        }

        # Very basic check: at least one valid keyword should be present
        filter_lower = filter_str.lower()
        has_valid_keyword = any(keyword in filter_lower for keyword in valid_keywords)

        if not has_valid_keyword and not filter_str.isdigit():
            logger.warning(
                f"BPF filter '{filter_str}' doesn't contain recognized keywords. "
                "It may be invalid. Common keywords: tcp, udp, icmp, port, host, src, dst"
            )

        return filter_str

    @staticmethod
    def validate_duration(duration: Optional[int]) -> Optional[int]:
        """
        Validate capture duration

        Args:
            duration: Duration in seconds

        Returns:
            Validated duration or None

        Raises:
            ValidationError: If duration is invalid
        """
        if duration is None:
            return None

        if duration <= 0:
            raise ValidationError("Duration must be a positive integer")

        if duration > 86400:  # 24 hours
            logger.warning(
                f"Duration is very long ({duration} seconds = {duration/3600:.1f} hours). "
                "This may consume significant resources."
            )

        return duration

    @staticmethod
    def validate_positive_integer(value: Optional[int], name: str, max_value: Optional[int] = None) -> Optional[int]:
        """
        Validate a positive integer value

        Args:
            value: Integer value to validate
            name: Name of the parameter for error messages
            max_value: Optional maximum allowed value

        Returns:
            Validated integer or None

        Raises:
            ValidationError: If value is invalid
        """
        if value is None:
            return None

        if not isinstance(value, int):
            raise ValidationError(f"{name} must be an integer, got {type(value).__name__}")

        if value <= 0:
            raise ValidationError(f"{name} must be positive, got {value}")

        if max_value is not None and value > max_value:
            raise ValidationError(f"{name} must be at most {max_value}, got {value}")

        return value

    @staticmethod
    def validate_contamination(contamination: float) -> float:
        """
        Validate contamination parameter for anomaly detection

        Args:
            contamination: Contamination ratio (0.0 to 0.5)

        Returns:
            Validated contamination value

        Raises:
            ValidationError: If value is invalid
        """
        if not isinstance(contamination, (int, float)):
            raise ValidationError(f"Contamination must be a number, got {type(contamination).__name__}")

        if contamination <= 0 or contamination >= 0.5:
            raise ValidationError(f"Contamination must be between 0 and 0.5, got {contamination}")

        return float(contamination)

    @staticmethod
    def validate_mode_requirements(mode: str, args: object) -> Tuple[bool, List[str]]:
        """
        Validate that required arguments are present for the given mode

        Args:
            mode: Analysis mode (realtime, offline, train)
            args: Parsed arguments object

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        if mode == 'realtime':
            # Realtime mode: interface is optional (auto-detected)
            # but if provided, should be valid
            if hasattr(args, 'interface') and args.interface:
                try:
                    InputValidator.validate_network_interface(args.interface)
                except ValidationError as e:
                    errors.append(str(e))

        elif mode == 'offline':
            # Offline mode requires PCAP file
            if not hasattr(args, 'pcap') or not args.pcap:
                errors.append("Offline mode requires --pcap argument")
            else:
                try:
                    InputValidator.validate_pcap_file(args.pcap)
                except ValidationError as e:
                    errors.append(str(e))

        elif mode == 'train':
            # Train mode requires training data
            if not hasattr(args, 'data') or not args.data:
                errors.append("Train mode requires --data argument")
            else:
                try:
                    InputValidator.validate_csv_file(args.data)
                except ValidationError as e:
                    errors.append(str(e))

        # Validate optional model file if provided
        if hasattr(args, 'model') and args.model:
            try:
                InputValidator.validate_model_file(args.model)
            except ValidationError as e:
                errors.append(str(e))

        # Validate optional preprocessor file if provided
        if hasattr(args, 'preprocessor') and args.preprocessor:
            try:
                InputValidator.validate_model_file(args.preprocessor)
            except ValidationError as e:
                errors.append(str(e))

        # Validate optional filter if provided
        if hasattr(args, 'filter') and args.filter:
            try:
                InputValidator.validate_bpf_filter(args.filter)
            except ValidationError as e:
                errors.append(str(e))

        # Validate optional duration if provided
        if hasattr(args, 'duration') and args.duration:
            try:
                InputValidator.validate_duration(args.duration)
            except ValidationError as e:
                errors.append(str(e))

        # Validate optional output path if provided
        if hasattr(args, 'output') and args.output:
            try:
                InputValidator.validate_output_path(args.output)
            except ValidationError as e:
                errors.append(str(e))

        return (len(errors) == 0, errors)

    @staticmethod
    def validate_email_address(email: str) -> bool:
        """
        Validate email address format

        Args:
            email: Email address string

        Returns:
            True if valid

        Raises:
            ValidationError: If email is invalid
        """
        # Basic email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(pattern, email):
            raise ValidationError(f"Invalid email address: {email}")

        return True

    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate URL format

        Args:
            url: URL string

        Returns:
            True if valid

        Raises:
            ValidationError: If URL is invalid
        """
        # Basic URL regex pattern
        pattern = r'^https?://[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})?(?:/.*)?$'

        if not re.match(pattern, url):
            raise ValidationError(f"Invalid URL: {url}. Must start with http:// or https://")

        return True
