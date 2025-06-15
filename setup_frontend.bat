@echo off
echo Setting up LifeConnect Frontend...

REM Remove existing frontend if corrupted
if exist frontend rmdir /s /q frontend

REM Create new React app
npx create-react-app frontend
cd frontend

REM Install additional dependencies
npm install axios react-router-dom lucide-react recharts @headlessui/react ethers
npm install -D tailwindcss postcss autoprefixer

REM Initialize Tailwind
npx tailwindcss init -p

echo Frontend setup complete!
echo Now copy the provided component files to their respective locations
pause
