const fs = require('fs');
const path = require('path');

const configsDir = path.join(process.cwd(), 'configs');

fs.readdir(configsDir, (err, files) => {
    files.forEach(file => {
        const filePath = path.join(configsDir, file);
        fs.readFile(filePath, 'utf-8', (err, data) => {
            const jsonData = JSON.parse(data);
            const formattedData = JSON.stringify(jsonData, null, 4);
            fs.writeFile(filePath, formattedData, 'utf-8', (err) => {});
        });
    });
});
