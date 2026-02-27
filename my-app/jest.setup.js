import '@testing-library/jest-dom';

// Mock fetch globally
global.fetch = jest.fn();

// Mock window.scrollIntoView
window.HTMLElement.prototype.scrollIntoView = jest.fn();

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';

// Reset mocks between tests
beforeEach(() => {
  jest.clearAllMocks();
});
