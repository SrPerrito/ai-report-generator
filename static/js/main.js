document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const uploadSection = document.getElementById('upload-section');
    const resultsSection = document.getElementById('results-section');
    const loader = document.getElementById('loader');
    const downloadBtn = document.getElementById('download-pdf');
    const progressSystem = document.getElementById('progress-system');
    const progressFill = document.getElementById('progress-fill');
    const progressValue = document.getElementById('progress-value');

    // ============================================
    // PARTICLE SYSTEM
    // ============================================
    const canvas = document.getElementById('particle-canvas');
    const ctx = canvas.getContext('2d');
    let particles = [];
    let mouseX = 0, mouseY = 0;

    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 2 + 0.5;
            this.speedX = (Math.random() - 0.5) * 0.5;
            this.speedY = (Math.random() - 0.5) * 0.5;
            this.opacity = Math.random() * 0.5 + 0.1;
            this.color = Math.random() > 0.5 ? '0, 245, 212' : '155, 93, 229';
        }

        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
            if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;

            const dx = mouseX - this.x;
            const dy = mouseY - this.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            if (distance < 150) {
                const force = (150 - distance) / 150;
                this.x -= dx * force * 0.02;
                this.y -= dy * force * 0.02;
            }
        }

        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${this.color}, ${this.opacity})`;
            ctx.fill();
        }
    }

    function initParticles() {
        particles = [];
        const count = Math.min(100, (canvas.width * canvas.height) / 15000);
        for (let i = 0; i < count; i++) particles.push(new Particle());
    }
    initParticles();

    function connectParticles() {
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                if (distance < 120) {
                    const opacity = (1 - distance / 120) * 0.15;
                    ctx.beginPath();
                    ctx.strokeStyle = `rgba(0, 245, 212, ${opacity})`;
                    ctx.lineWidth = 0.5;
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }
    }

    function animateParticles() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => { p.update(); p.draw(); });
        connectParticles();
        requestAnimationFrame(animateParticles);
    }
    animateParticles();

    window.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });

    // ============================================
    // DROP ZONE MOUSE TRACKING
    // ============================================
    dropZone.addEventListener('mousemove', (e) => {
        const rect = dropZone.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;
        dropZone.style.setProperty('--mouse-x', `${x}%`);
        dropZone.style.setProperty('--mouse-y', `${y}%`);
    });

    // ============================================
    // TOAST SYSTEM
    // ============================================
    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-icon"><i class="fas fa-${type === 'success' ? 'check' : 'exclamation'}"></i></div>
            <span class="toast-message">${message}</span>
        `;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 5000);
    }

    // ============================================
    // PROGRESS SIMULATION
    // ============================================
    function simulateProgress() {
        let progress = 0;
        const steps = document.querySelectorAll('.step');
        progressSystem.classList.remove('hidden');

        const interval = setInterval(() => {
            progress += Math.random() * 12;
            if (progress > 100) progress = 100;

            progressFill.style.width = `${progress}%`;
            progressValue.textContent = `${Math.round(progress)}%`;

            if (progress > 25) {
                steps[0].classList.add('completed');
                steps[0].classList.remove('active');
                steps[1].classList.add('active');
            }
            if (progress > 65) {
                steps[1].classList.add('completed');
                steps[1].classList.remove('active');
                steps[2].classList.add('active');
            }
            if (progress >= 100) {
                steps[2].classList.add('completed');
                steps[2].classList.remove('active');
                clearInterval(interval);
            }
        }, 400);
        return interval;
    }

    // ============================================
    // DROP ZONE EVENTS
    // ============================================
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleUpload(e.target.files[0]);
    });

    // ============================================
    // UPLOAD HANDLER
    // ============================================
    async function handleUpload(file) {
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!['.csv', '.xlsx'].includes(ext)) {
            showToast('Only CSV and XLSX files allowed', 'error');
            return;
        }
        if (file.size > 16 * 1024 * 1024) {
            showToast('File too large (max 16MB)', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        const progressInterval = simulateProgress();
        loader.classList.remove('hidden');
        dropZone.style.pointerEvents = 'none';
        dropZone.style.opacity = '0.5';

        try {
            const response = await fetch('/upload', { method: 'POST', body: formData });
            const data = await response.json();

            if (data.success) {
                clearInterval(progressInterval);
                progressFill.style.width = '100%';
                progressValue.textContent = '100%';
                showToast('Analysis complete!');
                displayResults(data);
            } else {
                clearInterval(progressInterval);
                showToast(data.error || 'Error occurred', 'error');
            }
        } catch (error) {
            clearInterval(progressInterval);
            showToast('Network error', 'error');
        } finally {
            loader.classList.add('hidden');
            dropZone.style.pointerEvents = 'auto';
            dropZone.style.opacity = '1';
            setTimeout(() => {
                progressSystem.classList.add('hidden');
                progressFill.style.width = '0%';
                document.querySelectorAll('.step').forEach(s => {
                    s.classList.remove('active', 'completed');
                });
                document.querySelector('.step').classList.add('active');
            }, 2000);
        }
    }

    // ============================================
    // DISPLAY RESULTS
    // ============================================
    function displayResults(data) {
        uploadSection.classList.add('hidden');
        resultsSection.classList.remove('hidden');

        document.getElementById('result-rows').textContent = data.rows || '0';
        document.getElementById('result-cols').textContent = data.columns || '0';
        document.getElementById('result-time').textContent = 'Just now';

        // Executive Summary
        const summary = data.analysis.executive_summary || 'No summary available.';
        document.getElementById('exec-summary').innerHTML = summary.replace(/\n/g, '<br>');

        // Key Metrics
        const metricsContainer = document.getElementById('key-metrics');
        metricsContainer.innerHTML = '';
        const metrics = data.analysis.key_metrics || [];
        metrics.forEach((metric, index) => {
            const item = document.createElement('div');
            item.className = 'metric-item';
            let name, value, description;
            if (typeof metric === 'object' && metric !== null) {
                name = metric.name || metric.metric || 'Metric ' + (index + 1);
                value = metric.value || 'N/A';
                description = metric.description || '';
            } else {
                name = 'Metric ' + (index + 1);
                value = String(metric);
                description = '';
            }
            item.innerHTML = `
                <div class="metric-name">${name}</div>
                <div class="metric-value">${value}</div>
                ${description ? `<div class="metric-desc">${description}</div>` : ''}
            `;
            metricsContainer.appendChild(item);
        });

        // AI Insights
        const insightsList = document.getElementById('ai-insights');
        insightsList.innerHTML = '';
        (data.analysis.insights || []).forEach(insight => {
            const li = document.createElement('li');
            li.innerHTML = `<div class="list-icon"><i class="fas fa-lightbulb"></i></div><span>${insight}</span>`;
            insightsList.appendChild(li);
        });

        // Recommendations
        const recsList = document.getElementById('ai-recs');
        recsList.innerHTML = '';
        (data.analysis.recommendations || []).forEach(rec => {
            const li = document.createElement('li');
            li.innerHTML = `<div class="list-icon"><i class="fas fa-rocket"></i></div><span>${rec}</span>`;
            recsList.appendChild(li);
        });

        // Anomalies
        const alertsList = document.getElementById('ai-alerts');
        alertsList.innerHTML = '';
        const anomalies = data.analysis.anomalies || [];
        if (anomalies.length === 0) {
            const li = document.createElement('li');
            li.innerHTML = `<div class="list-icon"><i class="fas fa-check"></i></div><span>No anomalies detected</span>`;
            alertsList.appendChild(li);
        } else {
            anomalies.forEach(alert => {
                const li = document.createElement('li');
                li.innerHTML = `<div class="list-icon"><i class="fas fa-exclamation"></i></div><span>${alert}</span>`;
                alertsList.appendChild(li);
            });
        }

        if (data.pdf_url) {
            downloadBtn.href = data.pdf_url;
            downloadBtn.classList.remove('hidden');
        }

        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // ============================================
    // RESET APP
    // ============================================
    window.resetApp = function () {
        uploadSection.classList.remove('hidden');
        resultsSection.classList.add('hidden');
        fileInput.value = '';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };
});