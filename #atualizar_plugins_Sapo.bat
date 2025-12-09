@echo off
chcp 65001 >nul

echo ==============================================
echo     Atualizando plugins via Git (branch main)
echo ==============================================
echo.

echo Verificando e removendo sparse-checkout / cone...
git sparse-checkout disable 2>nul
git config core.sparseCheckout false 2>nul

if exist .git\info\sparse-checkout (
    del .git\info\sparse-checkout
    echo Arquivo sparse-checkout removido.
)

echo Executando: git pull
git pull origin main --allow-unrelated-histories

echo.
echo ==============================================
echo        Atualização concluída!
echo ==============================================
pause
