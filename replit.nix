{pkgs}: {
  deps = [
    pkgs.python312Packages.aiohttp
    pkgs.gcc
    pkgs.unzip
  ];
}
