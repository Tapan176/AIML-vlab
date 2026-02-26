import React from 'react';
import './AboutUs.css';

const AboutUs = () => {
    return (
        <div className="about-page">
            <div className="about-hero">
                <h1>About <span className="accent">AIML Lab</span></h1>
                <p className="hero-subtitle">An interactive virtual laboratory for machine learning experimentation</p>
            </div>

            <div className="about-content">
                <section className="about-section">
                    <h2>🎯 Our Mission</h2>
                    <p>
                        AIML Lab is an open-source virtual laboratory designed to make machine learning
                        accessible to everyone. Whether you're a student learning the fundamentals or a
                        researcher experimenting with architectures, our platform provides an intuitive
                        interface to train, evaluate, and compare ML models — all from your browser.
                    </p>
                </section>

                <section className="about-section">
                    <h2>⚡ What You Can Do</h2>
                    <div className="feature-grid">
                        <div className="feature-card">
                            <span className="feature-icon">📈</span>
                            <h3>Regression</h3>
                            <p>Simple & Multivariable Linear Regression with real-time visualizations</p>
                        </div>
                        <div className="feature-card">
                            <span className="feature-icon">🎯</span>
                            <h3>Classification</h3>
                            <p>Logistic Regression, KNN, Decision Trees, Random Forest, SVM, Naïve Bayes</p>
                        </div>
                        <div className="feature-card">
                            <span className="feature-icon">🔮</span>
                            <h3>Clustering</h3>
                            <p>K-Means and DBSCAN with cluster visualization</p>
                        </div>
                        <div className="feature-card">
                            <span className="feature-icon">🧠</span>
                            <h3>Neural Networks</h3>
                            <p>CNN with custom layer builder, ANN with configurable architectures</p>
                        </div>
                        <div className="feature-card">
                            <span className="feature-icon">📝</span>
                            <h3>NLP</h3>
                            <p>Sentiment Analysis and Text Classification with TF-IDF pipelines</p>
                        </div>
                        <div className="feature-card">
                            <span className="feature-icon">🎨</span>
                            <h3>Generative AI</h3>
                            <p>StyleGAN for high-quality image generation</p>
                        </div>
                    </div>
                </section>

                <section className="about-section">
                    <h2>🛠️ Tech Stack</h2>
                    <div className="tech-grid">
                        <div className="tech-item">
                            <strong>Frontend</strong>
                            <span>React.js</span>
                        </div>
                        <div className="tech-item">
                            <strong>Backend</strong>
                            <span>Flask (Python)</span>
                        </div>
                        <div className="tech-item">
                            <strong>Database</strong>
                            <span>MongoDB</span>
                        </div>
                        <div className="tech-item">
                            <strong>ML Frameworks</strong>
                            <span>scikit-learn, TensorFlow/Keras, PyTorch</span>
                        </div>
                        <div className="tech-item">
                            <strong>Auth</strong>
                            <span>JWT Tokens</span>
                        </div>
                        <div className="tech-item">
                            <strong>Styling</strong>
                            <span>CSS Variables + Dark Mode</span>
                        </div>
                    </div>
                </section>

                <section className="about-section">
                    <h2>👥 Team</h2>
                    <p>
                        AIML Lab is built and maintained by passionate developers and ML enthusiasts.
                        We believe in open-source education and making AI tools accessible to all learners.
                    </p>
                </section>

                <section className="about-section">
                    <h2>📬 Get In Touch</h2>
                    <p>
                        Found a bug? Have a feature request? Want to contribute?
                        Check out our <a href="https://github.com/Tapan176/AIML-vlab" target="_blank" rel="noopener noreferrer">GitHub repository</a> or
                        open an issue.
                    </p>
                </section>
            </div>
        </div>
    );
};

export default AboutUs;
