{pkgs ? import <nixpkgs> {}}:
with pkgs;
with pkgs.lib; let
  inherit (python3.pkgs) typer colorama rich buildPythonApplication poetry-core; # rich 丰富色彩
in
  buildPythonApplication rec {
    version = "v0.1.0";
    src = ./.;
    pname = "sd";
    pyproject = true;
    nativeBuildInputs = [poetry-core installShellFiles];
    propagatedBuildInputs = [ typer colorama rich];
    postInstall = ''
      installShellCompletion --cmd sd --bash <($out/bin/sd --show-completion bash)
      installShellCompletion --cmd sd --zsh <($out/bin/sd --show-completion zsh)
      installShellCompletion --cmd sd --fish <($out/bin/sd --show-completion fish)
    '';
    meta = {
      description = "My system command line";
      platforms = platforms.all;
      maintainers = with maintainers; [shanyouli];
      license = licenses.gpl3;
    };
  }
