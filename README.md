# 🏆 Gold Price API

REST API for querying historical gold prices with automatic daily updates.

## 🚀 Features

- ✅ Automatic data extraction via Yahoo Finance (yfinance)
- ✅ 3-year historical backup
- ✅ Daily incremental updates via GitHub Actions
- ✅ Complete REST API built with FastAPI
- ✅ Efficient storage in Parquet format
- ✅ Fully automated CI/CD pipeline

## 📊 Available Data

- **Ticker**: GC=F (Gold Futures)
- **Period**: Last 3 years
- **Update Schedule**: Daily at 02:00 UTC
- **Fields**:
  - `date`: Record date
  - `max_price`: Daily maximum price
  - `min_price`: Daily minimum price
  - `closed_price`: Closing price

## 🛠️ Local Installation

```bash
# Clone the repository
git clone https://github.com/your-username/gold-price-api.git
cd gold-price-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create initial backup (first time only)
python src/extract_gold_data.py --backup

# Or run incremental update
python src/extract_gold_data.py
```

## 🚀 Running the API

```bash
# Start server
python src/api.py

# Or with uvicorn
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

Access: http://localhost:8000

Interactive documentation: http://localhost:8000/docs

## 📡 API Endpoints

### Information
- `GET /` - API information
- `GET /health` - Health check
- `GET /stats` - Data statistics

### Prices
- `GET /prices` - List prices (with pagination)
- `GET /prices/latest` - Latest available price
- `GET /prices/date/{date}` - Price for specific date
- `GET /prices/range?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Prices by date range

### Examples

```bash
# Latest price
curl http://localhost:8000/prices/latest

# Price for specific date
curl http://localhost:8000/prices/date/2024-01-10

# Prices within date range
curl "http://localhost:8000/prices/range?start_date=2024-01-01&end_date=2024-01-31"

# Statistics
curl http://localhost:8000/stats
```

## 🤖 GitHub Actions

### Automatic Execution
The pipeline runs automatically every day at 02:00 UTC.

### Manual Execution
1. Go to **Actions** → **Gold Price Data Pipeline**
2. Click **Run workflow**
3. Check "Create full backup" if needed
4. Click **Run workflow**

## 📁 Data Structure

```
dataset/
├── gold_backup.parquet    # Full backup (3 years)
├── gold_daily.parquet     # Consolidated incremental data
└── last_update.txt        # Last update checkpoint
```

## 🔧 Configuration

Edit `src/config.py` to customize:
- Asset ticker
- Backup period
- API settings
- Timezone

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest httpx

# Run tests
pytest tests/
```

## 🏗️ Project Structure

```
gold-price-api/
│
├── .github/
│   └── workflows/
│       └── gold_pipeline.yml          ← Automated CI/CD
│
├── src/
│   ├── __init__.py
│   ├── extract_gold_data.py           ← Data extraction with yfinance
│   ├── api.py                         ← FastAPI application
│   └── config.py                      ← Configuration settings
│
├── datasets/
│   ├── gold_backup.parquet            ← 3-year historical data
│   ├── gold_daily.parquet             ← Incremental data
│   └── last_update.txt                ← Update checkpoint
│
├── tests/
│   └── test_api.py                    ← API tests
│
├── .gitignore
├── requirements.txt
└── README.md
```

## 🎯 Deployment Checklist

- [ ] Clone repository
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Run initial backup (`python src/extract_gold_data.py --backup`)
- [ ] Configure GitHub Actions permissions (Settings → Actions → General → Read and write permissions)
- [ ] Test API locally (`python src/api.py`)
- [ ] Make first commit with data
- [ ] Verify workflow execution
- [ ] Test API endpoints
- [ ] Set up monitoring (optional)

## 🔒 Security Considerations

### Data Protection
- All data is sourced from public Yahoo Finance API
- No sensitive credentials required
- Repository can be safely made public

### GitHub Actions Permissions
Required permissions in workflow:
- ✅ `contents: write` - For automated commits
- ✅ Default `GITHUB_TOKEN` - No manual token creation needed

### Best Practices Implemented
- ✅ Automated updates with `[skip ci]` to prevent loops
- ✅ Data validation before commit
- ✅ Health checks and error handling
- ✅ Comprehensive logging

## 🚀 Deployment Options

### Option 1: Railway
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Option 2: Render
1. Connect GitHub repository
2. Select "Web Service"
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn src.api:app --host 0.0.0.0 --port $PORT`

### Option 3: Heroku
```bash
# Create Procfile
echo "web: uvicorn src.api:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
heroku create your-app-name
git push heroku main
```

### Option 4: Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t gold-price-api .
docker run -p 8000:8000 gold-price-api
```

## 📊 API Response Examples

### Latest Price
```json
{
  "date": "2024-01-10T00:00:00",
  "max_price": 2045.50,
  "min_price": 2030.25,
  "closed_price": 2042.75
}
```

### Statistics
```json
{
  "total_records": 756,
  "date_range_start": "2021-01-10T00:00:00",
  "date_range_end": "2024-01-10T00:00:00",
  "avg_closed_price": 1850.32,
  "max_closed_price": 2089.20,
  "min_closed_price": 1680.50
}
```

### Price List (with pagination)
```json
[
  {
    "date": "2024-01-10T00:00:00",
    "max_price": 2045.50,
    "min_price": 2030.25,
    "closed_price": 2042.75
  },
  {
    "date": "2024-01-09T00:00:00",
    "max_price": 2038.00,
    "min_price": 2025.50,
    "closed_price": 2035.25
  }
]
```

## 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Contribution Guidelines
- Follow PEP 8 style guide
- Add tests for new features
- Update documentation
- Ensure CI/CD passes

## 🐛 Troubleshooting

### Issue: No data returned from yfinance
**Solution**: Check if market is open. The API returns data for business days only.

### Issue: GitHub Actions permission denied
**Solution**: Go to Settings → Actions → General and enable "Read and write permissions"

### Issue: API returns 404
**Solution**: Ensure data files exist. Run `python src/extract_gold_data.py --backup` first.

### Issue: Large parquet files
**Solution**: Files are compressed by default. Consider archiving old data periodically.

## 📚 Additional Resources

- [yfinance Documentation](https://pypi.org/project/yfinance/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Parquet Format](https://parquet.apache.org/)

## 🎓 Learning Resources

- **FastAPI Tutorial**: https://fastapi.tiangolo.com/tutorial/
- **Pandas for Time Series**: https://pandas.pydata.org/docs/user_guide/timeseries.html
- **GitHub Actions CI/CD**: https://docs.github.com/en/actions/guides

## 🙏 Acknowledgments

- Yahoo Finance for providing free financial data
- FastAPI community for excellent documentation
- GitHub for free CI/CD with Actions

---

## 👤 Author

**Bruno Geraldine**
- [@BGeraldine-github](https://github.com/BrunoGeraldine)
- [LinkedIn](https://www.linkedin.com/in/brunogeraldine/)

**Made with ❤️ and Python** 🐍✨

## 📄 Licença

MIT License - look LICENSE to details

**⭐ If you find this project useful, please consider giving it a star!**