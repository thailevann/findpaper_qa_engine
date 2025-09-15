# FindPaper QA Engine - Frontend

A modern Next.js frontend for the FindPaper QA Engine, providing an intuitive interface for research question answering.

## Features

- **Smart Search Interface**: Clean, academic-focused design with advanced options
- **Real-time Results**: Comprehensive display of research findings with themes and citations
- **Model Selection**: Support for multiple OpenAI models (GPT-4o, GPT-4o Mini, etc.)
- **Query History**: Local storage of recent searches
- **Export Options**: Copy answers and download results
- **Responsive Design**: Mobile-first approach with excellent UX

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or pnpm
- FindPaper QA Engine backend running on `http://localhost:8000`

### Installation

1. Install dependencies:
   ```bash
   npm install
   # or
   pnpm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   # or
   pnpm dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

### Environment Configuration

Create a `.env.local` file in the frontend directory:

```bash
# API Base URL - Change this if your backend is running on a different port or host
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Enable debug mode for development
NEXT_PUBLIC_DEBUG=false
```

## API Integration

The frontend integrates with the FindPaper QA Engine backend through the following endpoints:

### Main Endpoint: `/qa`
- **Purpose**: Complete QA pipeline (finding + QA)
- **Method**: POST
- **Request**: 
  ```json
  {
    "query": "string",
    "limit": 50,
    "max_themes": 5,
    "model": "gpt-4o-mini"
  }
  ```

### Additional Endpoints
- `GET /health` - Health check
- `POST /search_passsages` - Finding pipeline only
- `POST /top_papers` - Finding pipeline with paper aggregation

## Supported Models

- **GPT-4o** - Best Quality
- **GPT-4o Mini** - Recommended (Default)
- **GPT-4 Turbo** - Fast GPT-4 variant
- **GPT-4** - Standard GPT-4
- **GPT-3.5 Turbo** - Fast & Cost-Effective

## Project Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── page.tsx           # Main page component
│   ├── layout.tsx          # App layout
│   └── globals.css         # Global styles
├── components/             # React components
│   ├── ui/                 # Radix UI components
│   ├── search-interface.tsx # Search form
│   ├── results-display.tsx # Results visualization
│   ├── loading-state.tsx   # Loading components
│   └── ...
├── lib/                    # Utilities and services
│   ├── api.ts              # API service
│   ├── utils.ts            # Helper functions
│   └── mock-data.ts        # Mock data for testing
├── hooks/                  # Custom React hooks
└── public/                 # Static assets
```

## Key Components

### SearchInterface
- Main search form with advanced options
- Model selection dropdown
- Example queries for quick testing
- Mock data option for development

### ResultsDisplay
- Comprehensive results visualization
- Theme-based organization
- Expandable sections for quotes and processing details
- Export functionality (copy/download)

### API Service (`lib/api.ts`)
- Centralized API communication
- Type-safe request/response handling
- Error handling and validation
- Model configuration

## Development

### Adding New Features

1. **New API Endpoints**: Add to `lib/api.ts`
2. **New UI Components**: Add to `components/` directory
3. **New Pages**: Add to `app/` directory
4. **Styling**: Use Tailwind CSS classes

### Testing

The app includes mock data functionality for testing without the backend:

1. Click "Try Mock Data" button
2. Uses realistic sample data
3. Simulates API delays

### Building for Production

```bash
npm run build
npm start
```

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Ensure backend is running on `http://localhost:8000`
   - Check `NEXT_PUBLIC_API_URL` in `.env.local`
   - Verify CORS settings in backend

2. **Model Selection Not Working**
   - Ensure OpenAI API key is set in backend environment
   - Check model availability in your OpenAI account

3. **Styling Issues**
   - Ensure Tailwind CSS is properly configured
   - Check for conflicting CSS classes

### Debug Mode

Enable debug mode by setting `NEXT_PUBLIC_DEBUG=true` in `.env.local` to see additional logging information.

## Contributing

1. Follow the existing code structure
2. Use TypeScript for type safety
3. Follow the established naming conventions
4. Test with both real API and mock data
5. Ensure responsive design works on all devices

## License

This project is part of the FindPaper QA Engine system.
