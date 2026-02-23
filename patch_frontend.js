const fs = require('fs');
const path = require('path');

const modelsDir = path.join(__dirname, 'frontend', 'src', 'components', 'Models');

function processFiles() {
    const files = fs.readdirSync(modelsDir).filter(f => f.endsWith('.js'));
    
    for (const file of files) {
        if (file === 'SimpleLinearRegression.js') continue;
        
        const filePath = path.join(modelsDir, file);
        let content = fs.readFileSync(filePath, 'utf-8');
        
        // Skip if already cached
        if (content.includes('localStorage.getItem') && content.includes('dataset')) {
            console.log(`Skipping ${file}`);
            continue;
        }

        const original = content;

        // Extract MODEL_CODE
        const modelCodeMatch = content.match(/const MODEL_CODE = ['"](.*?)['"]/);
        const modelCode = modelCodeMatch ? modelCodeMatch[1] : file.replace('.js', '').toLowerCase();
        
        // Determine allowed types
        const isZipType = modelCode.includes('cnn') || modelCode.includes('object');
        const allowedType = isZipType ? 'zip' : 'csv';

        // 1. Hook Injection
        const hookInjection = `
    useEffect(() => {
        const cached = localStorage.getItem(\`${modelCode}_dataset\`);
        if (cached) {
            try { setDatasetData(JSON.parse(cached)); } catch(e) {}
        }
    }, []);

    const handleDatasetSelect = (data) => {
        setDatasetData(data);
        if (data && data.filename) {
            localStorage.setItem(\`${modelCode}_dataset\`, JSON.stringify(data));
        } else {
            localStorage.removeItem(\`${modelCode}_dataset\`);
        }
    };
`;
        
        // Find the last useState to inject after
        const useStateRegex = /(const \[.*?, set.*?\] = useState\(.*?\);\s*\n)(?!.*useState)/s;
        content = content.replace(useStateRegex, match => match + hookInjection);

        // 2. Component replacement
        // Handle setDatasetData variations
        const datasetComponentRegex = /<ShowDataset\s+onDatasetUpload=\{setDatasetData\}\s*\/>/g;
        
        const newComponent = `<ShowDataset onDatasetUpload={handleDatasetSelect} allowedTypes={['${allowedType}']} />
                {datasetData && datasetData.filename && (
                    <div style={{ marginTop: '10px', color: '#34c759' }}>
                        ✓ Cached dataset: <strong>{datasetData.filename}</strong>
                    </div>
                )}`;

        content = content.replace(datasetComponentRegex, newComponent);

        if (content !== original) {
            fs.writeFileSync(filePath, content, 'utf-8');
            console.log(`Updated ${file}`);
        }
    }
}

processFiles();
