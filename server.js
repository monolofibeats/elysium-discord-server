const express = require('express');
const cors = require('cors');
const app = express();
const PORT = 3001;

app.use(cors());

// Pfad zur submissions.json
app.get('/submissions', (req, res) => {
  res.sendFile(__dirname + '/submissions.json');
});

app.listen(PORT, () => {
  console.log(`Server läuft auf http://localhost:${PORT}`);
});
