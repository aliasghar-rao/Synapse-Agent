export interface AgentBid {
  agentId: string;
  taskId: string;
  confidence: number;
  expertise: number;
  culturalRelevance: number;
  estimatedTime: number;
  resourceCost: number;
}

export interface ConsensusResult {
  selectedAgent: string;
  consensusScore: number;
  minorityReports: string[];
  culturalAdaptations: Record<string, any>;
}

export interface SwarmDecision {
  taskId: string;
  decision: any;
  confidence: number;
  participatingAgents: string[];
  culturalContext: string;
}

class AdvancedSwarmConsensus {
  private consensusThreshold: number;
  private culturalWeights: Map<string, number>;
  private agentExpertise: Map<string, number>;
  private decisionHistory: SwarmDecision[];

  constructor(threshold: number = 0.7) {
    this.consensusThreshold = threshold;
    this.culturalWeights = new Map();
    this.agentExpertise = new Map();
    this.decisionHistory = [];
  }

  // Auction-based task allocation with cultural weighting
  async auctionBasedAllocation(
    taskId: string, 
    bids: AgentBid[], 
    culturalContext: string
  ): Promise<ConsensusResult> {
    // Handle empty bids case
    if (!bids || bids.length === 0) {
      return {
        selectedAgent: 'default',
        consensusScore: 0,
        minorityReports: [],
        culturalAdaptations: {}
      };
    }
    
    // Calculate composite scores for each bid
    const scoredBids = bids.map(bid => ({
      ...bid,
      compositeScore: this.calculateCompositeScore(bid, culturalContext)
    }));

    // Sort by composite score
    scoredBids.sort((a, b) => b.compositeScore - a.compositeScore);

    // Check if top bid meets consensus threshold
    const topBid = scoredBids[0] || { agentId: 'default' };
    const consensusScore = await this.validateConsensus(scoredBids, culturalContext);

    // Generate minority reports from non-selected high-scoring agents
    const minorityReports = scoredBids
      .slice(1, 4) // Top 3 alternatives
      .filter(bid => bid.compositeScore > 0.6)
      .map(bid => `Agent ${bid.agentId}: Alternative approach with ${bid.confidence} confidence`);

    return {
      selectedAgent: topBid.agentId,
      consensusScore,
      minorityReports,
      culturalAdaptations: topBid ? await this.generateCulturalAdaptations(topBid, culturalContext) : {}
    };
  }

  // Expertise-weighted voting for complex decisions
  async expertiseWeightedVoting(
    proposals: Array<{ agentId: string; proposal: any; confidence: number }>,
    culturalContext: string
  ): Promise<SwarmDecision> {
    // Handle empty proposals case
    if (!proposals || proposals.length === 0) {
      return {
        taskId: `decision_${Date.now()}`,
        decision: null,
        confidence: 0,
        participatingAgents: [],
        culturalContext
      };
    }
    
    const votes = new Map<string, number>();
    const expertiseWeights = new Map<string, number>();
    
    // Calculate expertise weights based on historical performance
    for (const proposal of proposals) {
      const expertise = this.agentExpertise.get(proposal.agentId) || 0.5;
      const culturalWeight = this.culturalWeights.get(culturalContext) || 1.0;
      const adjustedWeight = expertise * culturalWeight * proposal.confidence;
      
      expertiseWeights.set(proposal.agentId, adjustedWeight);
      votes.set(proposal.agentId, adjustedWeight);
    }

    // Find consensus through weighted voting
    const totalWeight = Array.from(votes.values()).reduce((sum, weight) => sum + weight, 0);
    const sortedVotes = Array.from(votes.entries()).sort((a, b) => b[1] - a[1]);
    
    const winner = sortedVotes[0] || ['', 0];
    const consensusStrength = totalWeight > 0 ? winner[1] / totalWeight : 0;

    // Build decision with cultural context
    const decision: SwarmDecision = {
      taskId: `decision_${Date.now()}`,
      decision: proposals.find(p => p.agentId === winner[0])?.proposal || null,
      confidence: consensusStrength,
      participatingAgents: proposals.map(p => p.agentId),
      culturalContext
    };

    // Store for learning
    this.decisionHistory.push(decision);
    
    return decision;
  }

  // Peer review network for quality assurance
  async peerReviewConsensus(
    content: any,
    reviewers: string[],
    culturalContext: string
  ): Promise<{ approved: boolean; feedback: string[]; culturalScore: number }> {
    const reviews = await Promise.all(
      reviewers.map(reviewerId => this.simulateReview(content, reviewerId, culturalContext))
    );

    const approvalRate = reviews.filter(r => r.approved).length / reviews.length;
    const culturalScore = reviews.reduce((sum, r) => sum + r.culturalScore, 0) / reviews.length;
    
    const feedback = reviews
      .filter(r => r.feedback)
      .map(r => r.feedback);

    return {
      approved: approvalRate >= this.consensusThreshold,
      feedback,
      culturalScore
    };
  }

  // Dynamic consensus adaptation based on task complexity
  async adaptiveConsensus(
    taskComplexity: 'simple' | 'moderate' | 'complex',
    agents: string[],
    culturalContext: string
  ): Promise<{ method: string; threshold: number; participants: string[] }> {
    let method: string;
    let threshold: number;
    let participants: string[];

    switch (taskComplexity) {
      case 'simple':
        method = 'single_expert';
        threshold = 0.6;
        participants = [this.selectTopExpert(agents, culturalContext)];
        break;
      
      case 'moderate':
        method = 'expertise_weighted';
        threshold = 0.7;
        participants = this.selectTopExperts(agents, culturalContext, 3);
        break;
      
      case 'complex':
        method = 'full_swarm_consensus';
        threshold = 0.8;
        participants = agents;
        break;
    }

    return { method, threshold, participants };
  }

  // Private helper methods
  private calculateCompositeScore(bid: AgentBid, culturalContext: string): number {
    const culturalBonus = this.culturalWeights.get(culturalContext) || 1.0;
    const expertiseBonus = this.agentExpertise.get(bid.agentId) || 0.5;
    
    return (
      bid.confidence * 0.3 +
      bid.expertise * 0.25 +
      bid.culturalRelevance * 0.2 * culturalBonus +
      (1 / bid.estimatedTime) * 0.15 +
      (1 / bid.resourceCost) * 0.1 +
      expertiseBonus * 0.1
    );
  }

  private async validateConsensus(
    bids: Array<AgentBid & { compositeScore: number }>, 
    culturalContext: string
  ): Promise<number> {
    // Handle empty bids case
    if (!bids || bids.length === 0) {
      return 0;
    }
    
    const topScore = bids[0]?.compositeScore || 0;
    const secondScore = bids[1]?.compositeScore || 0;
    
    // Consensus strength based on score gap and cultural alignment
    const scoreGap = topScore - secondScore;
    const culturalAlignment = this.culturalWeights.get(culturalContext) || 1.0;
    
    return Math.min(scoreGap * culturalAlignment, 1.0);
  }

  private async generateCulturalAdaptations(
    bid: AgentBid, 
    culturalContext: string
  ): Promise<Record<string, any>> {
    // This would integrate with your Cultural Intelligence Service
    // Using bid information for more personalized cultural adaptations
    const expertiseLevel = this.agentExpertise.get(bid.agentId) || 0.5;
    
    return {
      language: culturalContext.split('_')[0] || 'en',
      formality: this.getCulturalFormality(culturalContext),
      timePreference: this.getCulturalTimePreference(culturalContext),
      communicationStyle: this.getCommunicationStyle(culturalContext),
      agentExpertise: expertiseLevel,
      customizations: {
        colorScheme: this.getCulturalColors(culturalContext),
        layout: this.getCulturalLayout(culturalContext)
      }
    };
  }

  private async simulateReview(
    content: any, 
    reviewerId: string, 
    culturalContext: string
  ): Promise<{ approved: boolean; feedback: string; culturalScore: number }> {
    // Simulate peer review based on agent expertise and cultural context
    const expertise = this.agentExpertise.get(reviewerId) || 0.5;
    const culturalWeight = this.culturalWeights.get(culturalContext) || 1.0;
    
    // Use content size as a factor in approval probability
    const contentComplexity = content ? JSON.stringify(content).length / 1000 : 1;
    const approvalProbability = (expertise * culturalWeight) / (1 + contentComplexity * 0.1);
    
    const approved = Math.random() < approvalProbability;
    const culturalScore = expertise * culturalWeight;
    
    return {
      approved,
      feedback: approved ? "Approved with minor suggestions" : "Requires cultural adaptation",
      culturalScore
    };
  }

  private selectTopExpert(agents: string[], culturalContext: string): string {
    return agents.reduce((best, current) => {
      const currentScore = (this.agentExpertise.get(current) || 0) * 
                          (this.culturalWeights.get(culturalContext) || 1);
      const bestScore = (this.agentExpertise.get(best) || 0) * 
                       (this.culturalWeights.get(culturalContext) || 1);
      return currentScore > bestScore ? current : best;
    });
  }

  private selectTopExperts(agents: string[], culturalContext: string, count: number): string[] {
    return agents
      .map(agent => ({
        agent,
        score: (this.agentExpertise.get(agent) || 0) * 
               (this.culturalWeights.get(culturalContext) || 1)
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, count)
      .map(item => item.agent);
  }

  // Cultural context helpers
  private getCulturalFormality(context: string): 'high' | 'medium' | 'low' {
    // Implementation would consult your Cultural Intelligence Service
    if (context.includes('japan') || context.includes('korea')) return 'high';
    if (context.includes('germany') || context.includes('uk')) return 'medium';
    return 'low';
  }

  private getCulturalTimePreference(context: string): 'punctual' | 'flexible' | 'relaxed' {
    if (context.includes('germany') || context.includes('japan')) return 'punctual';
    if (context.includes('spain') || context.includes('italy')) return 'flexible';
    return 'relaxed';
  }

  private getCommunicationStyle(context: string): 'direct' | 'indirect' | 'high_context' {
    if (context.includes('germany') || context.includes('netherlands')) return 'direct';
    if (context.includes('japan') || context.includes('korea')) return 'high_context';
    return 'indirect';
  }

  private getCulturalColors(context: string): string[] {
    // Return culturally appropriate color schemes
    if (context.includes('china')) return ['#DC143C', '#FFD700', '#000000'];
    if (context.includes('india')) return ['#FF9933', '#FFFFFF', '#138808'];
    return ['#0066CC', '#FFFFFF', '#333333']; // Default
  }

  private getCulturalLayout(context: string): 'rtl' | 'ltr' | 'vertical' {
    if (context.includes('arabic') || context.includes('hebrew')) return 'rtl';
    if (context.includes('japanese') && context.includes('traditional')) return 'vertical';
    return 'ltr';
  }

  // Public methods for learning and adaptation
  public updateAgentExpertise(agentId: string, performance: number): void {
    const current = this.agentExpertise.get(agentId) || 0.5;
    const updated = (current * 0.8) + (performance * 0.2); // Weighted average
    this.agentExpertise.set(agentId, Math.max(0.1, Math.min(1.0, updated)));
  }

  public updateCulturalWeights(context: string, effectiveness: number): void {
    const current = this.culturalWeights.get(context) || 1.0;
    const updated = (current * 0.9) + (effectiveness * 0.1);
    this.culturalWeights.set(context, Math.max(0.5, Math.min(2.0, updated)));
  }

  public getConsensusMetrics(): {
    totalDecisions: number;
    averageConfidence: number;
    culturalCoverage: number;
  } {
    const totalDecisions = this.decisionHistory.length;
    const averageConfidence = this.decisionHistory.reduce((sum, d) => sum + d.confidence, 0) / totalDecisions;
    const uniqueCultures = new Set(this.decisionHistory.map(d => d.culturalContext)).size;
    
    return {
      totalDecisions,
      averageConfidence,
      culturalCoverage: uniqueCultures
    };
  }
}

export default AdvancedSwarmConsensus;
