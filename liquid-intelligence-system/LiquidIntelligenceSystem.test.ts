import { LiquidIntelligenceSystem } from './LiquidIntelligenceSystem';
import { StreamAbsorptionEngine } from './learning-engines/StreamAbsorptionEngine';
import { ImmersionSimulator } from './immersion-simulation/ImmersionSimulator';
import { MediaCaptureSystem } from './media-processing/MediaCaptureSystem';

// Mock the external dependencies
jest.mock('./learning-engines/StreamAbsorptionEngine');
jest.mock('./immersion-simulation/ImmersionSimulator');
jest.mock('./media-processing/MediaCaptureSystem');

describe('LiquidIntelligenceSystem', () => {
  let liquidIntelligenceSystem: LiquidIntelligenceSystem;
  const mockConfig = {
    target_language: 'spanish',
    learning_intensity: 'intensive',
    cultural_context: 'latin_american',
    user_sources: {},
    learning_preferences: {}
  };

  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    
    // Create a new instance of LiquidIntelligenceSystem before each test
    liquidIntelligenceSystem = new LiquidIntelligenceSystem(mockConfig);
  });

  describe('Initialization', () => {
    test('should create an instance of LiquidIntelligenceSystem', () => {
      expect(liquidIntelligenceSystem).toBeInstanceOf(LiquidIntelligenceSystem);
    });

    test('should initialize with the correct configuration', () => {
      expect(liquidIntelligenceSystem['config']).toEqual(mockConfig);
    });

    test('should initialize all core components', () => {
      expect(liquidIntelligenceSystem['streamAbsorptionEngine']).toBeInstanceOf(StreamAbsorptionEngine);
      expect(liquidIntelligenceSystem['immersionSimulator']).toBeInstanceOf(ImmersionSimulator);
      expect(liquidIntelligenceSystem['mediaCaptureSystem']).toBeInstanceOf(MediaCaptureSystem);
    });
  });

  describe('Rapid Language Fluency', () => {
    test('should initiate the language fluency process', async () => {
      // Mock the internal methods
      liquidIntelligenceSystem['initializeLearningEnvironment'] = jest.fn().mockResolvedValue(undefined);
      liquidIntelligenceSystem['activateMultiStreamAbsorption'] = jest.fn().mockResolvedValue(undefined);
      liquidIntelligenceSystem['initiateImmersionSimulation'] = jest.fn().mockResolvedValue(undefined);
      liquidIntelligenceSystem['enableOsmoticAbsorption'] = jest.fn().mockResolvedValue(undefined);
      liquidIntelligenceSystem['activateDreamStateLearning'] = jest.fn().mockResolvedValue(undefined);
      liquidIntelligenceSystem['initiateEmotionalResonanceLearning'] = jest.fn().mockResolvedValue(undefined);
      liquidIntelligenceSystem['activateStreamConsciousnessProcessing'] = jest.fn().mockResolvedValue(undefined);
      liquidIntelligenceSystem['optimizeKnowledgeStructures'] = jest.fn().mockResolvedValue(undefined);
      liquidIntelligenceSystem['monitorProgress'] = jest.fn().mockResolvedValue({ fluency_level: 0.95, time_to_fluency: '48 hours' });

      const result = await liquidIntelligenceSystem.achieveRapidLanguageFluency('spanish');
      
      expect(result.fluency_level).toBeGreaterThan(0.9);
      expect(result.time_to_fluency).toBeDefined();
      
      // Verify all methods were called
      expect(liquidIntelligenceSystem['initializeLearningEnvironment']).toHaveBeenCalled();
      expect(liquidIntelligenceSystem['activateMultiStreamAbsorption']).toHaveBeenCalled();
      expect(liquidIntelligenceSystem['initiateImmersionSimulation']).toHaveBeenCalled();
      expect(liquidIntelligenceSystem['enableOsmoticAbsorption']).toHaveBeenCalled();
      expect(liquidIntelligenceSystem['activateDreamStateLearning']).toHaveBeenCalled();
      expect(liquidIntelligenceSystem['initiateEmotionalResonanceLearning']).toHaveBeenCalled();
      expect(liquidIntelligenceSystem['activateStreamConsciousnessProcessing']).toHaveBeenCalled();
      expect(liquidIntelligenceSystem['optimizeKnowledgeStructures']).toHaveBeenCalled();
      expect(liquidIntelligenceSystem['monitorProgress']).toHaveBeenCalled();
    });

    test('should handle errors during fluency process', async () => {
      // Mock one of the internal methods to throw an error
      liquidIntelligenceSystem['initializeLearningEnvironment'] = jest.fn().mockRejectedValue(new Error('Initialization failed'));
      
      await expect(liquidIntelligenceSystem.achieveRapidLanguageFluency('spanish'))
        .rejects
        .toThrow('Initialization failed');
    });
  });

  describe('Learning Environment Initialization', () => {
    test('should initialize the learning environment with correct parameters', async () => {
      const mockUI = {
        initialize: jest.fn().mockResolvedValue(undefined),
        adaptToProficiency: jest.fn().mockResolvedValue(undefined),
        integrateMediaStreams: jest.fn().mockResolvedValue(undefined)
      };
      
      // @ts-ignore - Mocking private property for testing
      liquidIntelligenceSystem['immersiveUI'] = mockUI;
      
      await liquidIntelligenceSystem['initializeLearningEnvironment']();
      
      expect(mockUI.initialize).toHaveBeenCalled();
      expect(mockUI.adaptToProficiency).toHaveBeenCalledWith('beginner');
      expect(mockUI.integrateMediaStreams).toHaveBeenCalled();
    });
  });

  describe('Multi-Stream Absorption', () => {
    test('should activate multi-stream absorption', async () => {
      const mockEngine = {
        initializeRegionalSources: jest.fn().mockResolvedValue(undefined),
        startProcessing: jest.fn().mockResolvedValue(undefined)
      };
      
      // @ts-ignore - Mocking private property for testing
      liquidIntelligenceSystem['streamAbsorptionEngine'] = mockEngine;
      
      await liquidIntelligenceSystem['activateMultiStreamAbsorption']();
      
      expect(mockEngine.initializeRegionalSources).toHaveBeenCalled();
      expect(mockEngine.startProcessing).toHaveBeenCalled();
    });
  });

  describe('Immersion Simulation', () => {
    test('should initiate immersion simulation', async () => {
      const mockSimulator = {
        initializeScenarios: jest.fn().mockResolvedValue(undefined),
        startSimulation: jest.fn().mockResolvedValue(undefined)
      };
      
      // @ts-ignore - Mocking private property for testing
      liquidIntelligenceSystem['immersionSimulator'] = mockSimulator;
      
      await liquidIntelligenceSystem['initiateImmersionSimulation']();
      
      expect(mockSimulator.initializeScenarios).toHaveBeenCalled();
      expect(mockSimulator.startSimulation).toHaveBeenCalled();
    });
  });

  describe('Progress Monitoring', () => {
    test('should monitor progress and return metrics', async () => {
      // @ts-ignore - Mocking private properties for testing
      liquidIntelligenceSystem['fluencyMetrics'] = {
        vocabulary_acquired: 5000,
        cultural_competence: 0.85,
        retention_rate: 0.92,
        contextual_usage: 0.88
      };
      
      const progress = await liquidIntelligenceSystem['monitorProgress']();
      
      expect(progress.fluency_level).toBeGreaterThan(0.8);
      expect(progress.time_to_fluency).toBeDefined();
      expect(progress.metrics).toBeDefined();
    });
  });
});
