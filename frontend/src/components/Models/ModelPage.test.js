import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

// Isolate ModelPage's own logic: stub the network/localStorage-backed children
// and hooks so we test the config-driven rendering, not their internals.
vi.mock('../Dataset/ShowDataset', () => ({ default: () => null }));
vi.mock('../shared/HyperparamPanel', () => ({ default: () => null }));
vi.mock('../shared/ModelInfoPanel', () => ({ default: () => null }));
vi.mock('../shared/CachedDatasetBadge', () => ({ default: () => null }));
vi.mock('../shared/ImageCarousel', () => ({ default: () => null }));
vi.mock('../DownloadTrainedModel/DownloadTrainedModel', () => ({ default: () => null }));
vi.mock('../DownloadResultsZip/DownloadResultsZip', () => ({ default: () => null }));
vi.mock('../DownloadModelPredictions/DownloadModelPredictions', () => ({ default: () => null }));
vi.mock('../../hooks/useDatasetCache', () => ({ default: () => ({ datasetData: null, handleDatasetSelect: () => {} }) }));
vi.mock('../../hooks/useReplaySession', () => ({ default: () => ({ hyperparams: {}, restoredResults: null }) }));
vi.mock('../../hooks/useModelTrain', () => ({ default: () => ({ train: vi.fn(), loading: false, error: '', results: null }) }));

import ModelPage from './ModelPage';
import { MODEL_PAGE_CONFIG } from './modelPageConfig';

const MIGRATED = [
  'simple_linear_regression', 'multivariable_linear_regression', 'logistic_regression',
  'knn', 'decision_tree', 'random_forest', 'svm', 'naive_bayes', 'k_means', 'dbscan',
  'gradient_boosting', 'xgboost', 'sentiment_analysis', 'text_classification',
];

describe('MODEL_PAGE_CONFIG', () => {
  it('has a complete entry for every migrated classical model', () => {
    for (const code of MIGRATED) {
      const c = MODEL_PAGE_CONFIG[code];
      expect(c, `missing config: ${code}`).toBeTruthy();
      expect(typeof c.endpoint).toBe('string');
      expect(typeof c.title).toBe('string');
      expect(typeof c.heading).toBe('string');
      expect(Array.isArray(c.metrics) && c.metrics.length > 0).toBe(true);
      for (const m of c.metrics) {
        expect(m.label).toBeTruthy();
        expect(m.key || m.get).toBeTruthy();
      }
    }
  });
});

describe('ModelPage', () => {
  it('renders a classification model: title + run button, no NLP inputs', () => {
    render(<ModelPage modelCode="knn" />);
    expect(screen.getByText('K-Nearest Neighbors')).toBeTruthy();
    expect(screen.getByText('▶ Run Model')).toBeTruthy();
    expect(screen.queryByText(/Text Column/)).toBeNull();
  });

  it('renders an NLP model with the text/label column inputs + custom labels', () => {
    render(<ModelPage modelCode="sentiment_analysis" />);
    expect(screen.getByText('Sentiment Analysis')).toBeTruthy();
    expect(screen.getByText('▶ Analyze Sentiment')).toBeTruthy();
    expect(screen.getByText(/Text Column/)).toBeTruthy();
    expect(screen.getByText(/Label Column/)).toBeTruthy();
  });

  it('renders the manual X/y inputs for the regression models', () => {
    render(<ModelPage modelCode="simple_linear_regression" />);
    expect(screen.getByText('Simple Linear Regression')).toBeTruthy();
    expect(screen.getByText('X (comma separated)')).toBeTruthy();
  });
});
