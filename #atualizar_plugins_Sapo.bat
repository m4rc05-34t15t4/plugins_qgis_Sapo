@echo off
chcp 65001 >nul

echo ==============================================
echo     Atualizando plugins via Git (branch main)
echo ==============================================
echo.

echo Executando: git pull
git pull

echo.
echo ==============================================
echo        Atualização concluída!
echo ==============================================
pause
