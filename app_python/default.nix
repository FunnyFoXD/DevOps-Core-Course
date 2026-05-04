{ pkgs ? import <nixpkgs> { } }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
    prometheus-client
    python-json-logger
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall

    mkdir -p "$out/bin"
    cp app.py "$out/bin/devops-info-service.py"
    chmod +x "$out/bin/devops-info-service.py"

    makeWrapper ${pkgs.python3}/bin/python "$out/bin/devops-info-service" \
      --add-flags "$out/bin/devops-info-service.py" \
      --prefix PYTHONPATH : "$PYTHONPATH"

    runHook postInstall
  '';
}
