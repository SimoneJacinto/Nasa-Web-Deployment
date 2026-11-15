
const { useState, useEffect } = React;


// NAVIGATION
function Navbar({ currentPage, goToPage }) {
    const pages = ["home", "how", "explore", "about"];

    return (
        <nav className="navbar">
            <div className="logo" onClick={() => goToPage("home")}>
                EARTH <span>JUKEBOX</span>
            </div>

            <div className="nav-links">
                {pages.map((page) => (
                    <a
                        key={page}
                        href={"#" + page}
                        className={currentPage === page ? "active" : ""}
                        onClick={(event) => {
                            event.preventDefault();
                            goToPage(page);
                        }}
                    >
                        {page === "how" ? "How It Works" :
                         page.charAt(0).toUpperCase() + page.slice(1)}
                    </a>
                ))}
            </div>
        </nav>
    );
}


// HOME PAGE
function HomePage({ goToExplore }) {
    return (
        <div className="home-page">

            <header className="hero-background">
                <div className="hero-grid"></div>

                <div className="hero-content">
                    <div className="eyebrow">
                        <span className="pulse-dot"></span>
                        EXPERIENCE EARTH DIFFERENTLY
                    </div>

                    <h1>
                        Hear the Earth.
                        <br />
                        <span>Explore the unseen.</span>
                    </h1>

                    <p>
                        What if you could hear the movement of our planet?
                        Earth Jukebox transforms NASA Earth science imagery
                        into sound, making invisible environmental data
                        accessible through listening.
                    </p>

                    <button
                        className="primary-button"
                        onClick={goToExplore}
                    >
                        Explore Wind Speed <span>↗</span>
                    </button>
                </div>

                <div className="hero-earth">
                    <img
                        className="earth-image"
                        src="https://images.unsplash.com/photo-1614730321146-b6fa6a46bcb4?auto=format&fit=crop&w=1200&q=85"
                        alt="Earth viewed from space"
                    />

                    <div className="earth-orbit orbit-one"></div>
                    <div className="earth-orbit orbit-two"></div>

                    <div className="earth-tag">
                        <span className="pulse-dot"></span>
                        WIND SPEED / LIVE DATA
                    </div>
                </div>

                <div className="hero-coordinates">
                    01 / EARTH SYSTEMS
                </div>

                <div className="hero-bottom">
                    <span>NASA EARTH SCIENCE</span>
                    <span>DATA → SOUND → ACCESSIBILITY</span>
                </div>
            </header>


            <section className="intro-section">
                <div className="section-label">01 — THE IDEA</div>

                <div className="intro-heading">
                    Science you can
                    <span> hear.</span>
                </div>

                <p className="intro-description">
                    Earth Jukebox creates a new way to experience
                    environmental information. By translating wind speed
                    data into audio, we make complex visual information
                    easier to experience through sound.
                </p>
            </section>


            <section className="home-feature-section">
                <div className="section-label">02 — WHAT YOU CAN DO</div>

                <div className="feature-cards">
                    <div className="feature-card">
                        <span className="feature-number">01</span>
                        <h3>Upload</h3>
                        <p>
                            Choose a NASA Earth science image showing
                            wind speed information.
                        </p>
                    </div>

                    <div className="feature-card">
                        <span className="feature-number">02</span>
                        <h3>Transform</h3>
                        <p>
                            Our processing system reads image data
                            and maps it into values.
                        </p>
                    </div>

                    <div className="feature-card">
                        <span className="feature-number">03</span>
                        <h3>Listen</h3>
                        <p>
                            Experience the mapped wind speed information
                            through generated audio.
                        </p>
                    </div>
                </div>
            </section>


            <section className="home-cta">
                <p>READY TO EXPERIENCE THE PLANET DIFFERENTLY?</p>
                <button
                    className="primary-button"
                    onClick={goToExplore}
                >
                    Enter the Sound Studio ↗
                </button>
            </section>
        </div>
    );
}


// HOW IT WORKS PAGE
function HowPage() {
    return (
        <section className="inner-page">
            <div className="page-hero">
                <div className="page-hero-index">01 / PROCESS</div>
                <h1>From image<br /><span>to sound.</span></h1>
                <p>
                    A simple process that transforms Earth science
                    imagery into an audio experience.
                </p>
            </div>

            <div className="timeline">
                <div className="timeline-step">
                    <div className="timeline-marker">01</div>
                    <div className="timeline-content">
                        <span>UPLOAD</span>
                        <h2>Choose your image</h2>
                        <p>
                            Upload a supported PNG or JPG image containing
                            NASA wind speed information.
                        </p>
                    </div>
                    <div className="timeline-visual visual-image">
                        <span>IMAGE INPUT</span>
                        <div className="mini-wave">〰 〰 〰</div>
                    </div>
                </div>

                <div className="timeline-step">
                    <div className="timeline-marker">02</div>
                    <div className="timeline-content">
                        <span>PROCESS</span>
                        <h2>Translate the data</h2>
                        <p>
                            The processing system extracts image information
                            and maps it into numerical values.
                        </p>
                    </div>
                    <div className="timeline-visual">
                        <span>DATA MAPPING</span>
                        <div className="mini-bars">
                            <i></i><i></i><i></i><i></i><i></i>
                        </div>
                    </div>
                </div>

                <div className="timeline-step">
                    <div className="timeline-marker">03</div>
                    <div className="timeline-content">
                        <span>LISTEN</span>
                        <h2>Experience the sound</h2>
                        <p>
                            The mapped values are converted into audio
                            so that users can listen to the data.
                        </p>
                    </div>
                    <div className="timeline-visual visual-audio">
                        <span>AUDIO OUTPUT</span>
                        <div className="mini-wave">∿ ∿ ∿ ∿</div>
                    </div>
                </div>
            </div>

            <div className="process-ending">
                VISUAL DATA. AUDITORY EXPERIENCE.
            </div>
        </section>
    );
}


// ABOUT PAGE
function AboutPage() {
    return (
        <main className="inner-page about-page">

            <section className="page-hero">
                <div className="page-hero-index">
                    ABOUT THE PROJECT / 04
                </div>

                <h1>
                    Science, <span>beyond sight.</span>
                </h1>

                <p>
                    An interactive, web-based scientific exhibition
                    that makes complex visualisations easier to
                    understand through sound.
                </p>
            </section>


            <section className="about-content">

                <div className="about-block">

                    <span className="section-label">
                        01 / THE CONCEPT
                    </span>

                    <h2>Experience scientific data differently.</h2>

                    <p>
                        The project aims to create an interactive,
                        web-based exhibition that makes scientific
                        visualisations easier to understand through sound.
                    </p>

                    <p>
                        Scientific information is usually presented
                        through graphs, maps, images and animations.
                        However, these visual formats can be difficult
                        for blind and visually impaired people to understand.
                    </p>

                    <p>
                        Our platform aims to make this information more
                        accessible by pairing scientific visualisations
                        with pre-generated sounds that visitors can
                        explore through the website.
                    </p>

                </div>


                <div className="about-block about-highlight">

                    <span className="section-label">
                        02 / SYSTEM ARCHITECTURE
                    </span>

                    <h2>How the system works.</h2>

                    <p>
                        The project has two main stages: preparation
                        of the scientific exhibits and the visitor's
                        experience of those exhibits.
                    </p>


                    <div className="system-flowchart">

                        <div className="flowchart-stage">

                            <div className="flowchart-heading">
                                <span>01</span>

                                <div>
                                    <h3>Preparation Stage</h3>
                                    <p>
                                        Scientific information is processed
                                        and transformed into sound before
                                        website presentation.
                                    </p>
                                </div>
                            </div>


                            <div className="flowchart-steps">

                                <div className="flowchart-node">
                                    <span>01</span>
                                    <strong>Scientific Data</strong>
                                    <small>
                                        Original scientific information
                                    </small>
                                </div>

                                <div className="flowchart-connector">↓</div>

                                <div className="flowchart-node">
                                    <span>02</span>
                                    <strong>Image / Data Processing</strong>
                                    <small>
                                        Extracting relevant information
                                    </small>
                                </div>

                                <div className="flowchart-connector">↓</div>

                                <div className="flowchart-node">
                                    <span>03</span>
                                    <strong>Scientific Interpretation</strong>
                                    <small>
                                        Understanding the data values
                                    </small>
                                </div>

                                <div className="flowchart-connector">↓</div>

                                <div className="flowchart-node highlight-node">
                                    <span>04</span>
                                    <strong>Sonification</strong>
                                    <small>
                                        Transforming data into sound
                                    </small>
                                </div>

                                <div className="flowchart-connector">↓</div>

                                <div className="flowchart-node">
                                    <span>05</span>
                                    <strong>
                                        Storage of Audio and Visual Content
                                    </strong>
                                    <small>
                                        Saving the prepared exhibits
                                    </small>
                                </div>

                            </div>


                            <div className="flowchart-output">
                                PREPARED SCIENTIFIC EXHIBITS
                            </div>

                        </div>


                        <div className="stage-connection">
                            <span>PREPARED CONTENT</span>
                            <div>↓</div>
                        </div>


                        <div className="flowchart-stage visitor-stage">

                            <div className="flowchart-heading">
                                <span>02</span>

                                <div>
                                    <h3>Visitor Experience Stage</h3>
                                    <p>
                                        Visitors explore the prepared
                                        scientific exhibits through
                                        the website.
                                    </p>
                                </div>
                            </div>


                            <div className="flowchart-steps">

                                <div className="flowchart-node">
                                    <span>01</span>
                                    <strong>
                                        Stored Visualisations and Audio
                                    </strong>
                                    <small>
                                        Prepared scientific exhibits
                                    </small>
                                </div>

                                <div className="flowchart-connector">↓</div>

                                <div className="flowchart-node">
                                    <span>02</span>
                                    <strong>Website Display</strong>
                                    <small>
                                        Exhibits presented to visitors
                                    </small>
                                </div>

                                <div className="flowchart-connector">↓</div>

                                <div className="flowchart-node">
                                    <span>03</span>
                                    <strong>User Interaction</strong>
                                    <small>
                                        Selecting and exploring exhibits
                                    </small>
                                </div>

                                <div className="flowchart-connector">↓</div>

                                <div className="flowchart-node highlight-node">
                                    <span>04</span>
                                    <strong>
                                        Audio Playback and Exploration
                                    </strong>
                                    <small>
                                        Listening to scientific data
                                        through sound
                                    </small>
                                </div>

                            </div>


                            <div className="flowchart-output visitor-output">
                                EXPLORE • LISTEN • UNDERSTAND
                            </div>

                        </div>

                    </div>


                    <p className="architecture-note">
                        The audio and visual content are prepared
                        beforehand. The website therefore focuses on
                        presenting the exhibits and allowing visitors
                        to interact with them, rather than processing
                        scientific data in real time.
                    </p>

                </div>


                <div className="about-block">

                    <span className="section-label">
                        03 / THE TECHNOLOGY
                    </span>

                    <h2>What is sonification?</h2>

                    <p>
                        Sonification is the process of converting data
                        into sound by linking different data properties
                        to different sound characteristics.
                    </p>

                    <p>
                        Instead of relying entirely on visual information,
                        listeners can recognise patterns and changes
                        through sound.
                    </p>


                    <div className="sonification-grid">

                        <div className="sonification-card">
                            <span>01</span>
                            <h3>Pitch</h3>
                            <p>
                                Can represent the magnitude of a value.
                            </p>
                        </div>

                        <div className="sonification-card">
                            <span>02</span>
                            <h3>Timbre</h3>
                            <p>
                                Can help distinguish between different
                                types of data.
                            </p>
                        </div>

                        <div className="sonification-card">
                            <span>03</span>
                            <h3>Rhythm</h3>
                            <p>
                                Can represent changes over time.
                            </p>
                        </div>

                        <div className="sonification-card">
                            <span>04</span>
                            <h3>Stereo Positioning</h3>
                            <p>
                                Can represent spatial information.
                            </p>
                        </div>

                    </div>


                    <p className="architecture-note">
                        By using consistent sound patterns and providing
                        audio explanations, visitors can understand what
                        they are hearing and how the data changes.
                    </p>

                </div>


                <div className="about-block final-goal">

                    <span className="section-label">
                        04 / OUR MISSION
                    </span>

                    <h2>Making science accessible to everyone.</h2>

                    <p>
                        The goal is to create an interactive scientific
                        exhibition where visitors can explore
                        visualisations, listen to their corresponding
                        sounds and understand patterns and changes
                        in scientific data.
                    </p>

                    <p>
                        By combining visual and audio experiences,
                        the platform aims to make scientific information
                        more accessible, engaging and easier to explore,
                        especially for people who cannot rely on visual
                        information alone.
                    </p>


                    <div className="mission-statement">
                        <span>SEE THE DATA.</span>
                        <span>HEAR THE PATTERNS.</span>
                        <span>EXPERIENCE SCIENCE.</span>
                    </div>

                </div>

            </section>

        </main>
    );
}


// EXPLORE PAGE
function ExplorePage({
    image,
    preview,
    handleImage,
    handleDrop,
    handleDragOver,
    removeImage,
    generateSound,
    loading,
    message,
    error,
    results,
    renderBars
}) {
    return (
        <section className="inner-page explore-page">

            <div className="page-hero">
                <div className="page-hero-index">02 / SOUND STUDIO</div>

                <h1>
                    Enter the
                    <br />
                    <span>wind studio.</span>
                </h1>

                <p>
                    Upload a wind speed visualization and transform
                    its information into sound.
                </p>
            </div>


            <div className="studio-title">
                <div>
                    <span className="section-label">YOUR WORKSPACE</span>
                    <h2>Wind Speed Sonification</h2>
                </div>

                <div className="phenomenon-selected">
                    <span className="pulse-dot"></span>
                    WIND SPEED
                </div>
            </div>


            <div className="studio-workspace">
                <div className="studio-grid">

                    <div className="studio-main">
                        <div className="studio-panel">

                            <div className="panel-topline">
                                <span>01 / IMAGE INPUT</span>
                                <span>PNG · JPG</span>
                            </div>

                            {!preview ? (
                                <label
                                    className="upload-target"
                                    htmlFor="image-upload"
                                    onDragEnter={handleDragOver}
                                    onDragOver={handleDragOver}
                                    onDrop={handleDrop}
                                >
                                    <div className="upload-icon">＋</div>
                                    <h3>Drop your image here</h3>
                                    <p>
                                        Select a wind speed visualization
                                        from your device.
                                    </p>

                                    <span className="upload-button">
                                        Choose Image
                                    </span>

                                    <input
                                        id="image-upload"
                                        type="file"
                                        accept=".png,.jpg,.jpeg,image/png,image/jpeg"
                                        onChange={handleImage}
                                    />
                                </label>
                            ) : (
                                <div className="preview-container">
                                    <img
                                        src={preview}
                                        alt="Uploaded wind speed visualization"
                                        className="preview"
                                    />

                                    <div className="preview-info">
                                        <span>IMAGE SELECTED</span>
                                        <strong>
                                            {image ? image.name : "Uploaded image"}
                                        </strong>
                                        <button
                                            className="remove-image"
                                            onClick={removeImage}
                                        >
                                            Remove image ×
                                        </button>
                                    </div>
                                </div>
                            )}

                            <button
                                className="generate-button"
                                onClick={generateSound}
                                disabled={loading || !image}
                            >
                                {loading ? (
                                    <>
                                        <span className="loading-spinner"></span>
                                        Processing wind data...
                                    </>
                                ) : (
                                    <>Generate Sound <span>↗</span></>
                                )}
                            </button>

                            {message && (
                                <p className="status" role="status">
                                    {message}
                                </p>
                            )}

                            {error && (
                                <p className="status error" role="alert">
                                    {error}
                                </p>
                            )}
                        </div>
                    </div>


                    <aside className="studio-side">
                        <div className="side-panel">
                            <span className="section-label">02 / DATA TYPE</span>
                            <h3>Wind Speed</h3>
                            <p>
                                Your uploaded image will be processed
                                as wind speed data.
                            </p>
                            <div className="workflow-item">
                                <span>01</span>
                                Image analysis
                            </div>
                            <div className="workflow-item">
                                <span>02</span>
                                Value mapping
                            </div>
                            <div className="workflow-item">
                                <span>03</span>
                                Audio generation
                            </div>
                        </div>

                        <div className="side-panel side-accent">
                            <span className="section-label">DID YOU KNOW?</span>
                            <h3>Feel the movement.</h3>
                            <p>
                                Wind is constantly moving around our planet.
                                Sonification offers another way to experience
                                information about that movement.
                            </p>
                        </div>
                    </aside>
                </div>
            </div>


            {results && (
                <section className="results-section">
                    <div className="results-title">
                        <span className="section-label">
                            03 / YOUR RESULTS
                        </span>
                        <h2>Data transformed.</h2>
                    </div>

                    <div className="results-grid">

                        <div className="result-panel">
                            <div className="panel-topline">
                                SCIENTIFIC DATA
                            </div>

                            <h3>Wind speed values</h3>

                            <p className="result-description">
                                {results.description}
                            </p>

                            {renderBars(results.values)}

                            <span className="unit-label">
                                UNIT: {results.unit || "Not specified"}
                            </span>

                            <details className="values-details">
                                <summary>View numerical values</summary>
                                <ol>
                                    {results.values.map((value, index) => (
                                        <li key={index}>
                                            {value} {results.unit || ""}
                                        </li>
                                    ))}
                                </ol>
                            </details>
                        </div>


                        <div className="result-panel audio-result">
                            <div className="panel-topline">
                                AUDIO EXPERIENCE
                            </div>

                            <div className="audio-art">
                                <div className="audio-orbit"></div>
                                <div className="audio-disc">♫</div>
                            </div>

                            <h3>Listen to the wind.</h3>

                            <p className="result-description">
                                Your wind speed sonification is ready.
                            </p>

                            <audio
                                controls
                                preload="metadata"
                                src={`data:audio/wav;base64,${results.audio}`}
                            >
                                Your browser does not support audio playback.
                            </audio>

                            <a
                                className="download-audio"
                                href={`data:audio/wav;base64,${results.audio}`}
                                download="earth-jukebox-wind-speed.wav"
                            >
                                Download Audio ↓
                            </a>
                        </div>

                    </div>
                </section>
            )}
        </section>
    );
}


// MAIN APP
function App() {
    const [currentPage, setCurrentPage] = useState("home");

    const [image, setImage] = useState(null);
    const [preview, setPreview] = useState("");

    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const [results, setResults] = useState(null);


    // PREVENT BROWSER FROM OPENING DROPPED FILES
    useEffect(() => {
        function preventDefault(event) {
            event.preventDefault();
        }

        window.addEventListener("dragover", preventDefault, true);
        window.addEventListener("drop", preventDefault, true);

        return () => {
            window.removeEventListener("dragover", preventDefault, true);
            window.removeEventListener("drop", preventDefault, true);
        };
    }, []);


    // CHANGE PAGE
    function goToPage(page) {
        setCurrentPage(page);
        window.scrollTo(0, 0);
    }


    // PROCESS IMAGE
    function processImage(selectedImage) {
        if (!["image/png", "image/jpeg"].includes(selectedImage.type)) {
            setError("Please select a PNG or JPG image.");
            return;
        }

        if (preview) {
            URL.revokeObjectURL(preview);
        }

        setImage(selectedImage);
        setPreview(URL.createObjectURL(selectedImage));
        setResults(null);
        setError("");
        setMessage("Image selected. Ready to process.");
    }


    // IMAGE UPLOAD THROUGH FILE SELECTOR
    function handleImage(event) {
        const selectedImage = event.target.files[0];

        if (selectedImage) {
            processImage(selectedImage);
        }

        event.target.value = "";
    }


    // PREVENT DEFAULT BROWSER DRAG BEHAVIOUR
    function handleDragOver(event) {
        event.preventDefault();
        event.stopPropagation();
    }


    // DRAG AND DROP IMAGE
    function handleDrop(event) {
        event.preventDefault();
        event.stopPropagation();

        const files = event.dataTransfer.files;
        const selectedImage = files && files[0];

        if (selectedImage) {
            processImage(selectedImage);
        }
    }


    // REMOVE IMAGE
    function removeImage() {
        if (preview) {
            URL.revokeObjectURL(preview);
        }

        setImage(null);
        setPreview("");
        setResults(null);
        setError("");
        setMessage("Image removed.");
    }


    // GENERATE SOUND
    async function generateSound() {
        if (!image) {
            setError("Please upload an image first.");
            return;
        }

        setLoading(true);
        setError("");
        setMessage("Processing your wind speed image...");

        const formData = new FormData();

        formData.append("image", image);
        formData.append("phenomenon", "wind_speed");

        try {
            const response = await fetch("/api/process", {
                method: "POST",
                body: formData
            });

            let data;

            try {
                data = await response.json();
            } catch {
                throw new Error("The server returned an invalid response.");
            }

            if (!response.ok) {
                throw new Error(data.error || "Processing failed.");
            }

            if (!data.audio || !Array.isArray(data.values)) {
                throw new Error("The server response is missing audio or data values.");
            }

            setResults(data);
            setMessage("Wind speed sonification completed.");

        } catch (err) {
            setError(err.message || "Something went wrong.");
            setMessage("");

        } finally {
            setLoading(false);
        }
    }


    // DATA BAR VISUALIZATION
    function renderBars(values) {
        if (!values || values.length === 0) {
            return <p>No numerical values were returned.</p>;
        }

        const numbers = values.map(Number);
        const maxValue = Math.max(...numbers.map(Math.abs), 1);

        return (
            <div
                className="data-bars"
                role="img"
                aria-label="Bar visualization of wind speed values"
            >
                {numbers.map((value, index) => {
                    const height = Math.max(
                        5,
                        (Math.abs(value) / maxValue) * 100
                    );

                    return (
                        <div
                            key={index}
                            className="data-bar"
                            style={{ height: height + "%" }}
                            title={`Value ${index + 1}: ${value}`}
                        />
                    );
                })}
            </div>
        );
    }


    return (
        <div className="app-shell">

            <Navbar
                currentPage={currentPage}
                goToPage={goToPage}
            />

            {currentPage === "home" && (
                <HomePage
                    goToExplore={() => goToPage("explore")}
                />
            )}

            {currentPage === "how" && <HowPage />}

            {currentPage === "about" && <AboutPage />}

            {currentPage === "explore" && (
                <ExplorePage
                    image={image}
                    preview={preview}
                    handleImage={handleImage}
                    handleDrop={handleDrop}
                    handleDragOver={handleDragOver}
                    removeImage={removeImage}
                    generateSound={generateSound}
                    loading={loading}
                    message={message}
                    error={error}
                    results={results}
                    renderBars={renderBars}
                />
            )}

            <footer className="footer">
                <div className="footer-logo">
                    EARTH <span>JUKEBOX</span>
                </div>

                <div className="footer-right">
                    MAKING EARTH SCIENCE MORE ACCESSIBLE
                </div>
            </footer>

        </div>
    );
}


ReactDOM.createRoot(
    document.getElementById("root")
).render(<App />);
