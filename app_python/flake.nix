{
  description = "DevOps Info Service reproducible builds with Nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  };

  outputs = { self, nixpkgs }:
    let
      system = builtins.currentSystem;
      pkgs = import nixpkgs { inherit system; };
      app = import ./default.nix { inherit pkgs; };
      dockerImage = import ./docker.nix { inherit pkgs; };
    in
    {
      packages.${system}.default = app;
      packages.${system}.dockerImage = dockerImage;

      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          python3
          python3Packages.fastapi
          python3Packages.uvicorn
          python3Packages.prometheus-client
          python3Packages.python-json-logger
        ];
      };
    };
}
