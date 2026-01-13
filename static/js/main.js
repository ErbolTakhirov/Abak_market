/**
 * ==============================================
 * GROCERY STORE - MAIN JAVASCRIPT
 * Production-ready, Vanilla JS
 * ==============================================
 */

(function () {
    'use strict';

    // ==============================================
    // DOM Ready Handler
    // ==============================================
    document.addEventListener('DOMContentLoaded', function () {
        initNavigation();
        initScrollEffects();
        initProductCards();
        initLazyLoading();
        initFilters();
        initFormValidation();
        initWhatsAppTracking();
    });

    // ==============================================
    // NAVIGATION
    // ==============================================
    function initNavigation() {
        const navToggle = document.getElementById('nav-toggle');
        const navMenu = document.getElementById('nav-menu');
        const header = document.getElementById('header');

        // Mobile menu toggle
        if (navToggle && navMenu) {
            navToggle.addEventListener('click', function () {
                this.classList.toggle('active');
                navMenu.classList.toggle('active');
                document.body.classList.toggle('menu-open');
            });

            // Close menu on link click
            navMenu.querySelectorAll('.nav-link').forEach(function (link) {
                link.addEventListener('click', function () {
                    navToggle.classList.remove('active');
                    navMenu.classList.remove('active');
                    document.body.classList.remove('menu-open');
                });
            });

            // Close menu on outside click
            document.addEventListener('click', function (e) {
                if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
                    navToggle.classList.remove('active');
                    navMenu.classList.remove('active');
                    document.body.classList.remove('menu-open');
                }
            });
        }

        // Header scroll effect
        if (header) {
            let lastScroll = 0;
            const scrollThreshold = 100;

            window.addEventListener('scroll', function () {
                const currentScroll = window.pageYOffset;

                if (currentScroll > scrollThreshold) {
                    header.classList.add('scrolled');
                } else {
                    header.classList.remove('scrolled');
                }

                lastScroll = currentScroll;
            }, { passive: true });
        }
    }

    // ==============================================
    // SCROLL EFFECTS
    // ==============================================
    function initScrollEffects() {
        // Smooth scroll for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
            anchor.addEventListener('click', function (e) {
                const targetId = this.getAttribute('href');
                if (targetId === '#') return;

                const target = document.querySelector(targetId);
                if (target) {
                    e.preventDefault();
                    const headerHeight = document.getElementById('header')?.offsetHeight || 72;
                    const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight;

                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });

        // Animate elements on scroll
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const animateOnScroll = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    animateOnScroll.unobserve(entry.target);
                }
            });
        }, observerOptions);

        document.querySelectorAll('.feature-card, .category-card, .product-card').forEach(function (el, index) {
            el.style.animationDelay = (index % 4) * 100 + 'ms';
            animateOnScroll.observe(el);
        });
    }

    // ==============================================
    // PRODUCT CARDS
    // ==============================================
    function initProductCards() {
        // Quick view on hover (for desktop)
        const productCards = document.querySelectorAll('.product-card');

        productCards.forEach(function (card) {
            const image = card.querySelector('.product-image');

            // Add touch feedback for mobile
            card.addEventListener('touchstart', function () {
                this.classList.add('touched');
            }, { passive: true });

            card.addEventListener('touchend', function () {
                this.classList.remove('touched');
            }, { passive: true });
        });

        // Track product clicks
        document.querySelectorAll('.product-card a').forEach(function (link) {
            link.addEventListener('click', function () {
                const productCard = this.closest('.product-card');
                const productName = productCard?.querySelector('.product-name')?.textContent;

                if (productName) {
                    trackEvent('product_click', {
                        product_name: productName
                    });
                }
            });
        });
    }

    // ==============================================
    // LAZY LOADING
    // ==============================================
    function initLazyLoading() {
        // Native lazy loading fallback
        if ('loading' in HTMLImageElement.prototype) {
            document.querySelectorAll('img[loading="lazy"]').forEach(function (img) {
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                }
            });
        } else {
            // Intersection Observer fallback
            const imageObserver = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.classList.add('loaded');
                        }
                        imageObserver.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(function (img) {
                imageObserver.observe(img);
            });
        }

        // Handle image load errors
        document.querySelectorAll('.product-image, .category-image').forEach(function (img) {
            img.addEventListener('error', function () {
                this.src = '/static/images/placeholder.png';
                this.classList.add('image-error');
            });
        });
    }

    // ==============================================
    // FILTERS
    // ==============================================
    function initFilters() {
        const filterForm = document.getElementById('filter-form');
        const filterSelects = document.querySelectorAll('.filter-select');

        filterSelects.forEach(function (select) {
            select.addEventListener('change', function () {
                if (filterForm) {
                    // Auto-submit on filter change
                    filterForm.submit();
                } else {
                    // Update URL with filter params
                    const url = new URL(window.location);
                    url.searchParams.set(this.name, this.value);
                    window.location.href = url.toString();
                }
            });
        });

        // Price range slider (if exists)
        const priceRange = document.getElementById('price-range');
        const priceValue = document.getElementById('price-value');

        if (priceRange && priceValue) {
            priceRange.addEventListener('input', function () {
                priceValue.textContent = formatPrice(this.value);
            });
        }
    }

    // ==============================================
    // FORM VALIDATION
    // ==============================================
    function initFormValidation() {
        const forms = document.querySelectorAll('form[data-validate]');

        forms.forEach(function (form) {
            form.addEventListener('submit', function (e) {
                let isValid = true;
                const requiredFields = form.querySelectorAll('[required]');

                requiredFields.forEach(function (field) {
                    if (!validateField(field)) {
                        isValid = false;
                    }
                });

                if (!isValid) {
                    e.preventDefault();
                    showNotification('Пожалуйста, заполните все обязательные поля', 'error');
                }
            });

            // Real-time validation
            form.querySelectorAll('input, select, textarea').forEach(function (field) {
                field.addEventListener('blur', function () {
                    validateField(this);
                });

                field.addEventListener('input', function () {
                    if (this.classList.contains('error')) {
                        validateField(this);
                    }
                });
            });
        });
    }

    function validateField(field) {
        const value = field.value.trim();
        const type = field.type;
        let isValid = true;
        let errorMessage = '';

        // Required check
        if (field.required && !value) {
            isValid = false;
            errorMessage = 'Это поле обязательно';
        }

        // Email validation
        if (isValid && type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Введите корректный email';
            }
        }

        // Phone validation
        if (isValid && type === 'tel' && value) {
            const phoneRegex = /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/;
            if (!phoneRegex.test(value.replace(/\s/g, ''))) {
                isValid = false;
                errorMessage = 'Введите корректный номер телефона';
            }
        }

        // Update field state
        field.classList.toggle('error', !isValid);

        // Show/hide error message
        let errorEl = field.parentNode.querySelector('.field-error');
        if (!isValid) {
            if (!errorEl) {
                errorEl = document.createElement('span');
                errorEl.className = 'field-error';
                field.parentNode.appendChild(errorEl);
            }
            errorEl.textContent = errorMessage;
        } else if (errorEl) {
            errorEl.remove();
        }

        return isValid;
    }

    // ==============================================
    // WHATSAPP TRACKING
    // ==============================================
    function initWhatsAppTracking() {
        // Track WhatsApp button clicks
        document.querySelectorAll('a[href*="wa.me"], .btn-whatsapp').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const productCard = this.closest('.product-card');
                const productName = productCard?.querySelector('.product-name')?.textContent;

                trackEvent('whatsapp_click', {
                    product_name: productName || 'general',
                    location: this.closest('section')?.className || 'unknown'
                });

                // Show confirmation message
                showNotification('Переход в WhatsApp...', 'success');
            });
        });
    }

    // ==============================================
    // UTILITY FUNCTIONS
    // ==============================================

    /**
     * Format price with currency
     */
    function formatPrice(amount, currency) {
        currency = currency || '₽';
        return new Intl.NumberFormat('ru-RU').format(amount) + ' ' + currency;
    }

    /**
     * Show notification toast
     */
    function showNotification(message, type) {
        type = type || 'info';

        // Remove existing notifications
        const existing = document.querySelector('.notification');
        if (existing) {
            existing.remove();
        }

        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'notification notification-' + type;
        notification.innerHTML = '<span>' + message + '</span>';

        // Add styles
        Object.assign(notification.style, {
            position: 'fixed',
            bottom: '100px',
            left: '50%',
            transform: 'translateX(-50%)',
            padding: '12px 24px',
            background: type === 'error' ? '#ef4444' : type === 'success' ? '#22c55e' : '#3b82f6',
            color: '#fff',
            borderRadius: '8px',
            boxShadow: '0 4px 14px rgba(0,0,0,0.15)',
            zIndex: '9999',
            animation: 'slideUp 0.3s ease'
        });

        document.body.appendChild(notification);

        // Auto remove after 3 seconds
        setTimeout(function () {
            notification.style.animation = 'slideDown 0.3s ease forwards';
            setTimeout(function () {
                notification.remove();
            }, 300);
        }, 3000);
    }

    /**
     * Track analytics event
     */
    function trackEvent(eventName, eventData) {
        // Google Analytics 4
        if (typeof gtag === 'function') {
            gtag('event', eventName, eventData);
        }

        // Yandex Metrika
        if (typeof ym === 'function') {
            ym(window.YM_COUNTER_ID, 'reachGoal', eventName, eventData);
        }

        // Console log for debugging
        console.log('Event:', eventName, eventData);
    }

    /**
     * Debounce function
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction() {
            const context = this;
            const args = arguments;
            const later = function () {
                timeout = null;
                func.apply(context, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Throttle function
     */
    function throttle(func, limit) {
        let inThrottle;
        return function () {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(function () {
                    inThrottle = false;
                }, limit);
            }
        };
    }

    // ==============================================
    // DYNAMIC STYLES
    // ==============================================
    const styleSheet = document.createElement('style');
    styleSheet.textContent = `
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateX(-50%) translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
        }
        
        @keyframes slideDown {
            from {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
            to {
                opacity: 0;
                transform: translateX(-50%) translateY(20px);
            }
        }
        
        .animate-in {
            animation: fadeInUp 0.5s ease forwards;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .product-card.touched {
            transform: scale(0.98);
        }
        
        .field-error {
            display: block;
            color: #ef4444;
            font-size: 0.75rem;
            margin-top: 4px;
        }
        
        input.error,
        select.error,
        textarea.error {
            border-color: #ef4444 !important;
        }
        
        .menu-open {
            overflow: hidden;
        }
    `;
    document.head.appendChild(styleSheet);

    // ==============================================
    // EXPOSE GLOBAL FUNCTIONS
    // ==============================================
    window.GroceryStore = {
        showNotification: showNotification,
        trackEvent: trackEvent,
        formatPrice: formatPrice
    };

})();
