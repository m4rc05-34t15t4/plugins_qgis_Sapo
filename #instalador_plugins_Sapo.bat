@echo off
chcp 65001 >nul

echo ==============================================
echo   Instalador de Plugins QGIS - Git Automático
echo   Repositório: m4rc05-34t15t4/plugins_qgis_Sapo (main)
echo ==============================================
echo.

REM 1 - Determinar automaticamente a pasta de plugins do QGIS
set "PLUGINS_DIR=%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins"

echo Pasta detectada de plugins:
echo %PLUGINS_DIR%
echo.

REM 2 - Criar a pasta caso não exista
if not exist "%PLUGINS_DIR%" (
    echo Criando pasta de plugins...
    mkdir "%PLUGINS_DIR%"
)

REM 3 - Entrar na pasta de plugins
echo Entrando na pasta de plugins...
cd /D "%PLUGINS_DIR%"

REM 4 - Verifica e inicializa o repositório Git
if not exist .git (
    echo Inicializando repositório Git na pasta atual...
    git init
) else (
    echo Repositório Git já existe. Pulando git init...
)

REM 5 - Definir branch principal como main
echo Definindo branch principal como main...
git symbolic-ref HEAD refs/heads/main

REM 6 - Remover sparse-checkout antigo
echo Removendo sparse-checkout antigo se existir...
git sparse-checkout disable 2>nul
git config core.sparseCheckout false 2>nul
del .git\info\sparse-checkout 2>nul

REM 7 - Configurar repositório remoto
echo Configurando origem remota...
git remote remove origin 2>nul
git remote add origin https://github.com/m4rc05-34t15t4/plugins_qgis_Sapo.git

REM 8 - Baixar todos os arquivos da branch main
echo Baixando plugins do GitHub...
git pull origin main --allow-unrelated-histories --force

REM 9 - Configurar rastreamento para "git pull"
echo Definindo rastreamento da branch main...
git branch --set-upstream-to=origin/main main

echo.
echo ==============================================
echo   Instalação concluída com sucesso!
echo   Plugins atualizados em:
echo   %PLUGINS_DIR%
echo ==============================================
pause
