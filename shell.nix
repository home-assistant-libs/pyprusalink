{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (ps: [
      ps.httpx
      ps.isort
      ps.flake8
      ps.black
    ]))
  ];
}

