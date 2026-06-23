const express = require('express');
const multer = require('multer');
const cors = require('cors');
const axios = require('axios');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(cors());
app.use(express.json());

const storage = multer.diskStorage({
  destination: 'uploads/',
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    cb(null, `${Date.now()}-${file.fieldname}${ext}`);
  }
});
const upload = multer({ storage });

const LANGFLOW_URL =
  'http://localhost:7861/api/v1/run/c0aac40d-b5be-4bc8-8673-b619266f53c9?stream=false';
const API_KEY = 'sk-W_zw3GbMeiWkX3zvUgVN0sLZqD6g8qm6QzqgpN9lBYs';

app.post('/analyze', upload.fields([{ name: 'build1' }, { name: 'build2' }]), async (req, res) => {
  let build1FilePath, build2FilePath;
  try {
    build1FilePath = path.resolve(req.files['build1'][0].path);
    build2FilePath = path.resolve(req.files['build2'][0].path);

    const payload = {
      output_type: 'chat',
      input_type: 'chat',
      input_value: 'Analyze the two build JSON files and give me the flaky test report.',
      session_id: 'flaky-test-session-' + Date.now(),
      tweaks: {
        'ReadFile-1': { path: build1FilePath },
        'ReadFile-2': { path: build2FilePath },
        'Prompt Template-1': {},
        'Groq-1': {}
      }
    };

    const response = await axios.post(LANGFLOW_URL, payload, {
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': API_KEY
      },
      timeout: 120000
    });

    res.json(response.data);
  } catch (error) {
    console.error('Langflow error:', error.response?.data || error.message);
    res.status(500).json({
      error: error.response?.data?.detail || error.message
    });
  } finally {
    if (build1FilePath && fs.existsSync(build1FilePath)) fs.unlinkSync(build1FilePath);
    if (build2FilePath && fs.existsSync(build2FilePath)) fs.unlinkSync(build2FilePath);
  }
});

const PORT = 3001;
app.listen(PORT, () => console.log(`Backend running on http://localhost:${PORT}`));
