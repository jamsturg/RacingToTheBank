# To The Bank - Racing Dashboard

A comprehensive racing dashboard built with Streamlit that provides real-time race analysis, form guides, and betting management.

## Features

- Real-time race tracking and analysis
- Advanced form analysis and predictions
- Statistical insights and track bias analysis
- Integrated betting management
- Account tracking and performance metrics
- Interactive data visualizations

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/RacingToTheBank.git
cd RacingToTheBank
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Update the values in `.env` with your configuration:
     ```
     PGHOST=localhost
     PGDATABASE=racing_db
     PGUSER=your_username
     PGPASSWORD=your_password
     PGPORT=5432
     
     PUNTING_FORM_API_KEY=your_api_key
     ```

4. Run the application:
```bash
streamlit run main.py
```

## Usage

1. Login using demo credentials:
   - Username: demo
   - Password: demo

2. Navigate through different sections:
   - Dashboard: Overview of account performance and live races
   - Race Analysis: Detailed race analysis with speed maps
   - Form Guide: Comprehensive form analysis for runners
   - Statistics: Track bias and market analysis
   - Betting: Place bets and track active bets
   - Account: Manage account settings and view history

## Components

- `main.py`: Main Streamlit application
- `advanced_racing_predictor.py`: Racing prediction algorithms
- `advanced_analytics.py`: Statistical analysis tools
- `advanced_form_analysis.py`: Form analysis components
- `account_management.py`: Account management functionality
- `tab_api_client.py`: TAB API integration

## Database Setup

1. Install PostgreSQL if not already installed
2. Create a new database:
```sql
CREATE DATABASE racing_db;
```
3. Update the database configuration in your `.env` file
4. The application will handle table creation and schema management

## API Configuration

1. Get your API key from [Punting Form](https://puntingform.com.au/)
2. Add your API key to the `.env` file:
```
PUNTING_FORM_API_KEY=your_api_key
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Data visualization using [Plotly](https://plotly.com/)
- Statistical analysis with [NumPy](https://numpy.org/) and [Pandas](https://pandas.pydata.org/)
- Database management with [PostgreSQL](https://www.postgresql.org/)
