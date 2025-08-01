// healthcare-agents-suite.config.ts
export const HealthcareAgentsSuite: AgentSuiteConfiguration = {
  suite_id: 'healthcare_diagnostics_v1',
  description: 'Medical diagnostic support and healthcare automation',
  agents: [
    {
      type: 'MedicalImagingAgent',
      capabilities: ['image_analysis', 'anomaly_detection', 'diagnostic_support'],
      cultural_adaptations: ['regional_health_beliefs', 'medical_communication_norms']
    },
    {
      type: 'PatientInteractionAgent',
      capabilities: ['symptom_analysis', 'patient_communication', 'triage_support'],
      cultural_adaptations: ['cultural_health_practices', 'patient_communication_styles']
    },
    {
      type: 'PharmacologyAgent',
      capabilities: ['drug_interaction_analysis', 'dosage_optimization', 'side_effect_prediction'],
      cultural_adaptations: ['regional_medication_practices', 'cultural_treatment_preferences']
    }
  ],
  coordination_patterns: ['peer_review', 'specialist_consultation'],
  compliance_requirements: ['HIPAA', 'GDPR', 'regional_medical_regulations']
};
