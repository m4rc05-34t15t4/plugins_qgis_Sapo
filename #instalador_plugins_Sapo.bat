@echo off
chcp 65001 >nul
echo ==============================================
echo   Instalador de Plugins - Git Completo
echo   Repositório: m4rc05-34t15t4/plugins (branch main)
echo ==============================================
echo.

REM 1 - Verifica e inicializa o repositório Git
if not exist .git (
    echo Inicializando repositório Git...
    git init
) else (
    echo Repositório Git já existe. Pulando git init...
)

REM 2 - Define a branch principal como "main"
echo Definindo branch principal como main...
git symbolic-ref HEAD refs/heads/main

REM 3 - DESATIVAR quaisquer configurações antigas de sparse-checkout
echo Removendo sparse-checkout antigo...
git sparse-checkout disable 2>nul
git config core.sparseCheckout false 2>nul
del .git\info\sparse-checkout 2>nul

REM 4 - Configura o repositório remoto
echo Configurando origem remota...
git remote remove origin 2>nul
git remote add origin https://github.com/m4rc05-34t15t4/plugins_qgis_Sapo.git

REM 5 - Baixa todos os arquivos da branch main
echo Baixando plugins do GitHub...
git pull origin main --allow-unrelated-histories --force

REM 6 - Define rastreamento para permitir "git pull" sem args
echo Definindo main para acompanhar origin/main...
git branch --set-upstream-to=origin/main main

echo.
echo ==============================================
echo   Instalação concluída com sucesso!
echo   Agora basta usar "git pull" para atualizar.
echo ==============================================
pause
