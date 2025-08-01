// financial-agents-suite.config.ts
export const FinancialAgentsSuite: AgentSuiteConfiguration = {
  suite_id: 'financial_services_v1',
  description: 'Comprehensive financial analysis and automation',
  agents: [
    {
      type: 'FraudDetectionAgent',
      capabilities: ['transaction_analysis', 'pattern_recognition', 'risk_assessment'],
      cultural_adaptations: ['regional_banking_norms', 'financial_communication_styles']
    },
    {
      type: 'CreditScoringAgent',
      capabilities: ['credit_analysis', 'regulatory_compliance', 'alternative_data_processing'],
      cultural_adaptations: ['regional_credit_practices', 'cultural_financial_behaviors']
    },
    {
      type: 'InvestmentAdvisorAgent',
      capabilities: ['portfolio_optimization', 'risk_management', 'market_analysis'],
      cultural_adaptations: ['regional_investment_preferences', 'cultural_risk_tolerance']
    }
  ],
  coordination_patterns: ['hierarchical', 'consensus_based'],
  resource_requirements: {
    cpu_cores: 8,
    memory_gb: 16,
    gpu_required: true
  }
};
