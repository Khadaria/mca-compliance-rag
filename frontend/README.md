# Frontend

This is the Vite frontend for CompliCS.

## Local Run

```powershell
npm install
$env:VITE_API_URL="http://localhost:8000"
npm run dev
```

## Production

Deploy this folder to Vercel with:
- root directory: `frontend`
- build command: `npm run build`
- output directory: `dist`

Required environment variable:
- `VITE_API_URL`
