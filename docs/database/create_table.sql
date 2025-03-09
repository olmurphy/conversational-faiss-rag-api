CREATE TABLE user_sessions (
    session_id UUID NOT NULL,
    user_id CHARACTER VARYING(40) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    device_type VARCHAR(255),
    other_session_metadata JSONB,
    PRIMARY KEY (session_id)
);

-- Index on user_id for efficient user-based queries
CREATE INDEX idx_user_id ON user_sessions (user_id);

-- Assuming user_info table exists and has user_id as primary key
ALTER TABLE user_sessions ADD CONSTRAINT fk_user_sessions_user_id FOREIGN KEY (user_id) REFERENCES user_info(user_id);

CREATE TABLE user_interactions (
    interaction_id UUID NOT NULL,
    session_id UUID NOT NULL,
    user_query TEXT,
    created_at TIMESTAMP NOT NULL,
    llm_response TEXT,
    edited_response TEXT,
    positive_feedback BOOLEAN,
    negative_feedback BOOLEAN,
    feedback_reason TEXT,
    rating INTEGER,
    interaction_time INTEGER,
    clicks INTEGER,
    scroll_depth FLOAT,
    number_of_turns INTEGER,
    PRIMARY KEY (interaction_id)
);

-- Create index on session_id for efficient lookups
CREATE INDEX idx_user_interactions_session_id ON user_interactions (session_id);

-- Add foreign key constraint
ALTER TABLE user_interactions ADD CONSTRAINT fk_user_interactions_session_id FOREIGN KEY (session_id) REFERENCES user_sessions(session_id);

CREATE TABLE rag_retrievals (
    retrieval_id UUID PRIMARY KEY NOT NULL,
    interaction_id UUID NOT NULL,
    rag_invocation_time INTEGER,
    retrieved_document_ids TEXT[],
    faiss_retrieval_time FLOAT,
    retrieved_document_count INTEGER,
    similarity_scores FLOAT[],
    retrieval_latency INTEGER,
    document_sources TEXT[],
    document_lenghts INTEGER[]
);

-- Index on interaction_id
CREATE INDEX idx_rag_interaction_id ON rag_retrievals (interaction_id);

-- Add foreign key constraint
ALTER TABLE rag_retrievals ADD CONSTRAINT fk_rag_retrievals_interaction_id FOREIGN KEY (interaction_id) REFERENCES user_interactions(interaction_id);

CREATE TABLE evaluation_metrics (
    evaluation_id UUID PRIMARY KEY,
    interaction_id UUID NOT NULL,
    accuracy FLOAT,
    correctness BOOLEAN,
    relevance FLOAT,
    coherence FLOAT,
    fluency FLOAT,
    completeness FLOAT,
    helpfulness FLOAT,
    toxicity FLOAT,
    sentiment VARCHAR(255), -- Using VARCHAR instead of STRING
    human_eval_score FLOAT,
    human_eval_notes TEXT,
    factual_consistency FLOAT,
    hallucination_score FLOAT
);

-- Index on interaction_id
CREATE INDEX idx_eval_interaction_id ON evaluation_metrics (interaction_id);

-- Add foreign key constraint
ALTER TABLE evaluation_metrics ADD CONSTRAINT fk_evaluation_metrics_interaction_id FOREIGN KEY (interaction_id) REFERENCES user_interactions(interaction_id);

CREATE TABLE llm_invocations (
    llm_invocation_id UUID PRIMARY KEY,
    interaction_id UUID NOT NULL,
    confidence_score FLOAT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    llm_latency INTEGER,
    llm_api_errors INTEGER,
    llm_temperature FLOAT,
    llm_top_p FLOAT,
    llm_top_k INTEGER,
    guardrails_triggered BOOLEAN,
    guardrail_violations JSON
);

-- Index on interaction_id
CREATE INDEX idx_llm_interaction_id ON llm_invocations (interaction_id);

-- Add foreign key constraint
ALTER TABLE llm_invocations ADD CONSTRAINT fk_llm_invocations_interaction_id FOREIGN KEY (interaction_id) REFERENCES user_interactions(interaction_id);