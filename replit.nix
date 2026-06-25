{pkgs}: {
  deps = [
    pkgs.pyflyby
    pkgs.python312Packages.aiohttp
    pkgs.gcc
    pkgs.unzip
  ];
}
