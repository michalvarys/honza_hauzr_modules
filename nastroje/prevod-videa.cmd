@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

rem ============================================================
rem  Prevod videa pro web Honza Hauzr
rem
rem  Pouziti: pretahni video (nebo vic videi) myssi na tenhle
rem  soubor. Vedle originalu vznikne "<nazev>-web.mp4", ktery
rem  se nahrava do Odoo. Original zustava nedotceny.
rem
rem  Co se deje a proc:
rem   - H.264 misto H.265: H.265 Firefox neprehraje vubec
rem     a Chrome jen na nekterych pocitacich.
rem   - nejdelsi strana na 1920 px: 4K na webu nikdo nepozna,
rem     ale stahuje se nekolikanasobne dele. Svisla videa
rem     zustanou svisla, orientace se nemeni.
rem   - crf 23: kvalita podle obsahu, ne pevny tok. Ze 25 Mbit/s
rem     vyjde zhruba 3 Mbit/s, tedy asi osmkrat mensi soubor.
rem   - yuv420p: bez tohohle nekdy nejde obraz na starsich
rem     telefonech, i kdyz jinak je soubor v poradku.
rem   - faststart: presune index na zacatek souboru, takze
rem     video jde spustit hned a neceka se na cely download.
rem ============================================================

set "FFMPEG="
where ffmpeg >nul 2>nul && set "FFMPEG=ffmpeg"
if not defined FFMPEG (
  for /d %%D in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*") do (
    for /d %%E in ("%%~D\ffmpeg-*") do (
      if exist "%%~E\bin\ffmpeg.exe" set "FFMPEG=%%~E\bin\ffmpeg.exe"
    )
  )
)
if not defined FFMPEG (
  echo.
  echo ffmpeg se nepodarilo najit. Nainstaluj ho prikazem:
  echo     winget install Gyan.FFmpeg
  echo.
  pause
  exit /b 1
)

if "%~1"=="" (
  echo.
  echo  Pretahni na tenhle skript video, ktere chces nahrat na web.
  echo  Muzes jich pretahnout i vic najednou.
  echo.
  pause
  exit /b 0
)

set "CHYBY=0"

:dalsi
if "%~1"=="" goto hotovo

echo.
echo ============================================================
echo  %~nx1
echo ============================================================

"%FFMPEG%" -hide_banner -loglevel error -stats -y -i "%~1" ^
  -vf "scale='min(1920,iw)':'min(1920,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2" ^
  -c:v libx264 -preset slow -crf 23 -profile:v high -level:v 4.1 -pix_fmt yuv420p ^
  -c:a aac -b:a 128k -ac 2 ^
  -movflags +faststart ^
  "%~dp1%~n1-web.mp4"

if errorlevel 1 (
  echo   PREVOD SELHAL
  set /a CHYBY+=1
) else (
  echo   hotovo: %~n1-web.mp4
)

shift
goto dalsi

:hotovo
echo.
if "%CHYBY%"=="0" (
  echo  Vsechno prevedeno. Soubory s koncovkou -web.mp4 nahraj v editoru
  echo  tlacitkem "Nahrat video". Originaly si nech, nejsou k nicemu potreba.
) else (
  echo  Dokonceno, ale %CHYBY% prevod/y selhal/y - viz vypis vyse.
)
echo.
pause
