"""map provided modules to packages"""
import re
import sys
from pathlib import Path

from packaging import utils as pkgutil

from .errors import PackageNotFoundError

def _parse_record(record):
    """Return a list of all top-level importable names from a distribution's RECORD"""
    python_names = set()
    for rec in record.splitlines():
        # every entry is made up of three parts
        name = rec.rsplit(',', 2)[0]
        # RECORD paths are not required to be in the style of native paths
        name = name.split('/', 1)[0].split('\\', 1)[0]
        if not (name.startswith('..') # relative paths are typically data and anyway not findable
            or '-' in name # skip the .dist-info paths
            # there are other characters that would invalidate lookup
        ):
            if name.endswith(".py"):
                name = name[:-3]
            python_names.add(name)
    return python_names

wheel_metadata_dir_pattern = re.compile(r"(?P<name>.*?)-\d+(\.\d+)*\.dist-info")
def provided_modules(package, search_paths=None):
    """Return a list of top-level modules provided by `package`

    By default searches sys.path for installed packages
    A package may not provide any modules, in which case an empty set is returned
    If the package cannot be found, raise a PackageNotFoundError
    """
    if search_paths is None:
        search_paths = sys.path
    package_name = pkgutil.canonicalize_name(package)

    for search_dir in search_paths:
        search = Path(search_dir)
        if not search.is_dir():
            continue
        for entry in search.iterdir():
            if entry.is_dir() and (match := wheel_metadata_dir_pattern.match(entry.name)):
                found_package = match.group("name")
                if pkgutil.canonicalize_name(found_package) == package_name:
                    # all valid wheels will have a RECORD file
                    return _parse_record((entry / "RECORD").read_text())
    raise PackageNotFoundError(package)
