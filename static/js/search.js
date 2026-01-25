/**
 * ==============================================
 * SMART SEARCH - JavaScript модуль
 * ==============================================
 * 
 * Умный поиск товаров с подсказками и автодополнением.
 * 
 * Использование:
 * 1. Подключите этот скрипт на страницу
 * 2. Добавьте HTML элемент поиска с id="search-input"
 * 3. Поиск автоматически инициализируется
 * 
 * Настройки можно изменить в объекте SEARCH_CONFIG
 */

(function () {
    'use strict';

    // ==============================================
    // КОНФИГУРАЦИЯ (можно донастроить)
    // ==============================================
    const SEARCH_CONFIG = {
        // Минимальная длина запроса для подсказок
        minQueryLength: 2,

        // Задержка перед отправкой запроса (мс)
        debounceDelay: 300,

        // API endpoints
        apiEndpoints: {
            search: '/api/catalog/search/',
            suggestions: '/api/catalog/search/suggestions/',
        },

        // Максимум подсказок
        maxSuggestions: 8,

        // Показывать категории в подсказках
        showCategories: true,

        // Показывать популярные запросы
        showPopularQueries: true,
    };

    // ==============================================
    // КЛАСС УМНОГО ПОИСКА
    // ==============================================
    class SmartSearch {
        constructor(inputElement, options = {}) {
            this.input = inputElement;
            this.config = { ...SEARCH_CONFIG, ...options };
            this.dropdown = null;
            this.debounceTimer = null;
            this.isOpen = false;
            this.selectedIndex = -1;
            this.suggestions = [];

            this.init();
        }

        init() {
            // Создаём dropdown для подсказок
            this.createDropdown();

            // Привязываем обработчики событий
            this.bindEvents();

            // Добавляем стили
            this.injectStyles();
        }

        createDropdown() {
            this.dropdown = document.createElement('div');
            this.dropdown.className = 'search-dropdown';
            this.dropdown.style.display = 'none';

            // Вставляем после input
            this.input.parentNode.style.position = 'relative';
            this.input.parentNode.appendChild(this.dropdown);
        }

        bindEvents() {
            // Ввод текста
            this.input.addEventListener('input', (e) => {
                this.handleInput(e.target.value);
            });

            // Фокус
            this.input.addEventListener('focus', () => {
                if (this.input.value.length >= this.config.minQueryLength) {
                    this.showDropdown();
                }
            });

            // Потеря фокуса
            this.input.addEventListener('blur', () => {
                // Задержка, чтобы успеть кликнуть по подсказке
                setTimeout(() => this.hideDropdown(), 200);
            });

            // Навигация клавишами
            this.input.addEventListener('keydown', (e) => {
                this.handleKeydown(e);
            });

            // Отправка формы
            const form = this.input.closest('form');
            if (form) {
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.performSearch(this.input.value);
                });
            }
        }

        handleInput(query) {
            clearTimeout(this.debounceTimer);

            if (query.length < this.config.minQueryLength) {
                this.hideDropdown();
                return;
            }

            // Debounce - ждём окончания ввода
            this.debounceTimer = setTimeout(() => {
                this.fetchSuggestions(query);
            }, this.config.debounceDelay);
        }

        async fetchSuggestions(query) {
            try {
                const url = `${this.config.apiEndpoints.suggestions}?q=${encodeURIComponent(query)}&limit=${this.config.maxSuggestions}`;
                const response = await fetch(url);
                const data = await response.json();

                if (data.success) {
                    this.suggestions = this.formatSuggestions(data);
                    this.renderDropdown();
                    this.showDropdown();
                }
            } catch (error) {
                console.error('Search error:', error);
            }
        }

        formatSuggestions(data) {
            const suggestions = [];

            // Добавляем товары
            if (data.products && data.products.length > 0) {
                data.products.forEach(product => {
                    suggestions.push({
                        type: 'product',
                        id: product.id,
                        name: product.name,
                        slug: product.slug,
                        price: product.formatted_price,
                        category: product.category,
                        categoryIcon: product.category_icon,
                        image: product.image_url,
                    });
                });
            }

            // Добавляем категории
            if (this.config.showCategories && data.categories && data.categories.length > 0) {
                data.categories.forEach(category => {
                    suggestions.push({
                        type: 'category',
                        id: category.id,
                        name: category.name,
                        slug: category.slug,
                        icon: category.icon,
                        count: category.products_count,
                    });
                });
            }

            // Добавляем популярные запросы
            if (this.config.showPopularQueries && data.queries && data.queries.length > 0) {
                data.queries.forEach(query => {
                    suggestions.push({
                        type: 'query',
                        query: query.query,
                        count: query.count,
                    });
                });
            }

            return suggestions;
        }

        renderDropdown() {
            if (this.suggestions.length === 0) {
                this.dropdown.innerHTML = `
                    <div class="search-empty">
                        <span class="search-empty-icon">🔍</span>
                        <span>Ничего не найдено</span>
                    </div>
                `;
                return;
            }

            let html = '';
            let currentType = null;

            this.suggestions.forEach((item, index) => {
                // Добавляем заголовок секции
                if (item.type !== currentType) {
                    currentType = item.type;
                    const sectionTitle = this.getSectionTitle(item.type);
                    if (sectionTitle) {
                        html += `<div class="search-section-title">${sectionTitle}</div>`;
                    }
                }

                html += this.renderItem(item, index);
            });

            this.dropdown.innerHTML = html;

            // Привязываем клики
            this.dropdown.querySelectorAll('.search-item').forEach((el, index) => {
                el.addEventListener('click', () => {
                    this.selectItem(index);
                });
                el.addEventListener('mouseenter', () => {
                    this.highlightItem(index);
                });
            });
        }

        getSectionTitle(type) {
            switch (type) {
                case 'product': return '🛒 Товары';
                case 'category': return '📁 Категории';
                case 'query': return '🔎 Популярные запросы';
                default: return null;
            }
        }

        renderItem(item, index) {
            const isSelected = index === this.selectedIndex;
            const selectedClass = isSelected ? 'search-item--selected' : '';

            switch (item.type) {
                case 'product':
                    return `
                        <div class="search-item search-item--product ${selectedClass}" data-index="${index}">
                            ${item.image ? `<img src="${item.image}" alt="${item.name}" class="search-item-image">` : '<div class="search-item-image search-item-image--empty">📦</div>'}
                            <div class="search-item-content">
                                <div class="search-item-name">${this.highlightMatch(item.name, this.input.value)}</div>
                                <div class="search-item-meta">
                                    <span class="search-item-category">${item.categoryIcon || ''} ${item.category}</span>
                                    <span class="search-item-price">${item.price}</span>
                                </div>
                            </div>
                        </div>
                    `;
                case 'category':
                    return `
                        <div class="search-item search-item--category ${selectedClass}" data-index="${index}">
                            <div class="search-item-icon">${item.icon || '📁'}</div>
                            <div class="search-item-content">
                                <div class="search-item-name">${this.highlightMatch(item.name, this.input.value)}</div>
                                <div class="search-item-count">${item.count} товаров</div>
                            </div>
                        </div>
                    `;
                case 'query':
                    return `
                        <div class="search-item search-item--query ${selectedClass}" data-index="${index}">
                            <div class="search-item-icon">🔍</div>
                            <div class="search-item-content">
                                <div class="search-item-name">${this.highlightMatch(item.query, this.input.value)}</div>
                            </div>
                        </div>
                    `;
                default:
                    return '';
            }
        }

        highlightMatch(text, query) {
            if (!query) return text;
            const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
            return text.replace(regex, '<mark>$1</mark>');
        }

        escapeRegex(string) {
            return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        }

        handleKeydown(e) {
            if (!this.isOpen) return;

            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    this.moveSelection(1);
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    this.moveSelection(-1);
                    break;
                case 'Enter':
                    e.preventDefault();
                    if (this.selectedIndex >= 0) {
                        this.selectItem(this.selectedIndex);
                    } else {
                        this.performSearch(this.input.value);
                    }
                    break;
                case 'Escape':
                    this.hideDropdown();
                    break;
            }
        }

        moveSelection(direction) {
            const newIndex = this.selectedIndex + direction;
            if (newIndex >= -1 && newIndex < this.suggestions.length) {
                this.highlightItem(newIndex);
            }
        }

        highlightItem(index) {
            this.selectedIndex = index;

            // Обновляем стили
            this.dropdown.querySelectorAll('.search-item').forEach((el, i) => {
                el.classList.toggle('search-item--selected', i === index);
            });
        }

        selectItem(index) {
            const item = this.suggestions[index];
            if (!item) return;

            switch (item.type) {
                case 'product':
                    window.location.href = `/catalog/product/${item.slug}/`;
                    break;
                case 'category':
                    window.location.href = `/catalog/menu/?category=${item.slug}`;
                    break;
                case 'query':
                    this.input.value = item.query;
                    this.performSearch(item.query);
                    break;
            }

            this.hideDropdown();
        }

        performSearch(query) {
            if (query.length < this.config.minQueryLength) return;

            // Редирект на страницу результатов поиска
            window.location.href = `/catalog/menu/?q=${encodeURIComponent(query)}`;
        }

        showDropdown() {
            this.dropdown.style.display = 'block';
            this.isOpen = true;
        }

        hideDropdown() {
            this.dropdown.style.display = 'none';
            this.isOpen = false;
            this.selectedIndex = -1;
        }

        injectStyles() {
            if (document.getElementById('smart-search-styles')) return;

            const styles = document.createElement('style');
            styles.id = 'smart-search-styles';
            styles.textContent = `
                /* Search Dropdown */
                .search-dropdown {
                    position: absolute;
                    top: calc(100% + 12px);
                    left: 0;
                    right: 0;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 15px 50px rgba(0, 0, 0, 0.12);
                    max-height: 420px;
                    overflow-y: auto;
                    z-index: 1000;
                    border: 1px solid rgba(0,0,0,0.05);
                    animation: searchSlideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    scrollbar-width: thin;
                    scrollbar-color: var(--menu-accent) transparent;
                }

                @keyframes searchSlideIn {
                    from { opacity: 0; transform: translateY(-10px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                .search-section-title {
                    padding: 16px 20px 8px;
                    font-size: 0.7rem;
                    font-weight: 800;
                    color: var(--menu-text-light);
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    background: rgba(0,0,0,0.02);
                }

                .search-item {
                    display: flex;
                    align-items: center;
                    gap: 16px;
                    padding: 14px 20px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    border-bottom: 1px solid rgba(0,0,0,0.03);
                }

                .search-item:last-child {
                    border-bottom: none;
                }

                .search-item:hover,
                .search-item--selected {
                    background: #FDF9F4;
                }

                .search-item-image {
                    width: 52px;
                    height: 52px;
                    border-radius: 12px;
                    object-fit: cover;
                    flex-shrink: 0;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                }

                .search-item-image--empty {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: #F5E6D3;
                    font-size: 1.5rem;
                    color: white;
                }

                .search-item-icon {
                    width: 44px;
                    height: 44px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: rgba(196, 149, 106, 0.1);
                    border-radius: 12px;
                    font-size: 1.25rem;
                    flex-shrink: 0;
                    color: var(--menu-accent);
                }

                .search-item-content {
                    flex: 1;
                    min-width: 0;
                }

                .search-item-name {
                    font-weight: 700;
                    font-size: 0.95rem;
                    color: var(--menu-text-dark);
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    margin-bottom: 2px;
                }

                .search-item-name mark {
                    background: rgba(196, 149, 106, 0.2);
                    color: var(--menu-text-dark);
                    padding: 0 1px;
                    border-radius: 3px;
                }

                .search-item-meta {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 0.8rem;
                }

                .search-item-category {
                    color: var(--menu-text-light);
                    font-weight: 500;
                }

                .search-item-price {
                    font-weight: 800;
                    color: var(--menu-accent-dark);
                }

                .search-item-count {
                    font-size: 0.75rem;
                    font-weight: 600;
                    color: var(--menu-text-light);
                }

                .search-empty {
                    padding: 40px 20px;
                    text-align: center;
                    color: var(--menu-text-light);
                }

                .search-empty-icon {
                    display: block;
                    font-size: 2.5rem;
                    margin-bottom: 12px;
                    opacity: 0.5;
                }

                /* Mobile responsive tweaks */
                @media (max-width: 768px) {
                    .search-dropdown {
                        position: fixed;
                        left: 12px;
                        right: 12px;
                        top: 85px; /* Adjust according to header height */
                        max-height: calc(85vh - 100px);
                        border-radius: 24px;
                    }
                    
                    .search-item {
                        padding: 16px 20px;
                    }
                }
            `;
            document.head.appendChild(styles);
        }
    }

    // ==============================================
    // АВТОИНИЦИАЛИЗАЦИЯ
    // ==============================================
    function initSearch() {
        // Ищем все поля поиска на странице
        const searchInputs = document.querySelectorAll('.search-input, #search-input, [data-smart-search]');

        searchInputs.forEach(input => {
            if (!input.hasAttribute('data-search-initialized')) {
                new SmartSearch(input);
                input.setAttribute('data-search-initialized', 'true');
            }
        });
    }

    // Инициализация при загрузке DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSearch);
    } else {
        initSearch();
    }

    // Экспортируем класс для ручной инициализации
    window.SmartSearch = SmartSearch;
    window.initSmartSearch = initSearch;
})();
