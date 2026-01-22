/**
 * CART LOGIC - ABAK MARKET
 * Handles local storage cart, UI updates, and WhatsApp checkout
 */

class ShoppingCart {
    constructor() {
        this.cart = JSON.parse(localStorage.getItem('abak_cart')) || [];
        this.whatsappNumber = document.body.dataset.whatsapp || '996700000000';
        this.init();
    }

    init() {
        this.renderFloatButton();
        this.renderCartDrawer();
        this.updateCartCount();
        this.bindEvents();
    }

    bindEvents() {
        // Toggle cart drawer
        document.addEventListener('click', (e) => {
            if (e.target.closest('.cart-float-btn') || e.target.closest('.open-cart')) {
                this.toggleCart(true);
            }
            if (e.target.closest('.cart-close') || (e.target.classList.contains('cart-overlay') && !e.target.closest('.cart-drawer'))) {
                this.toggleCart(false);
            }
        });

        // Add to cart buttons
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.add-to-cart-btn');
            if (btn) {
                e.preventDefault();
                const product = {
                    id: btn.dataset.id,
                    name: btn.dataset.name,
                    price: parseFloat(btn.dataset.price),
                    image: btn.dataset.image,
                    qty: 1
                };
                this.addItem(product);

                // Visual feedback
                const originalIcon = btn.innerHTML;
                btn.innerHTML = '✅';
                btn.style.background = '#27ae60';
                setTimeout(() => {
                    btn.innerHTML = originalIcon;
                    btn.style.background = '';
                }, 1000);
            }
        });

        // Cart actions (+, -, remove)
        const cartItemsContainer = document.querySelector('.cart-items');
        if (cartItemsContainer) {
            cartItemsContainer.addEventListener('click', (e) => {
                const itemId = e.target.closest('.cart-item')?.dataset.id;
                if (!itemId) return;

                if (e.target.closest('.qty-plus')) {
                    this.updateQty(itemId, 1);
                } else if (e.target.closest('.qty-minus')) {
                    this.updateQty(itemId, -1);
                } else if (e.target.closest('.cart-item-remove')) {
                    this.removeItem(itemId);
                }
            });
        }

        // WhatsApp Checkout
        const checkoutBtn = document.querySelector('.cart-whatsapp-btn');
        if (checkoutBtn) {
            checkoutBtn.addEventListener('click', () => this.checkoutWhatsApp());
        }
    }

    addItem(product) {
        const existing = this.cart.find(item => item.id === product.id);
        if (existing) {
            existing.qty += 1;
        } else {
            this.cart.push(product);
        }
        this.saveCart();
    }

    updateQty(id, delta) {
        const item = this.cart.find(item => item.id === id);
        if (item) {
            item.qty += delta;
            if (item.qty <= 0) {
                this.removeItem(id);
            } else {
                this.saveCart();
            }
        }
    }

    removeItem(id) {
        this.cart = this.cart.filter(item => item.id !== id);
        this.saveCart();
    }

    saveCart() {
        localStorage.setItem('abak_cart', JSON.stringify(this.cart));
        this.updateUI();
    }

    updateUI() {
        this.updateCartCount();
        this.renderCartItems();
        this.updateTotal();
    }

    updateCartCount() {
        const count = this.cart.reduce((sum, item) => sum + item.qty, 0);
        const floatBtn = document.querySelector('.cart-float-btn');
        let badge = floatBtn?.querySelector('.cart-count');

        if (count > 0) {
            if (floatBtn && !badge) {
                badge = document.createElement('span');
                badge.className = 'cart-count';
                floatBtn.appendChild(badge);
            }
            if (badge) badge.innerText = count;
            floatBtn.style.display = 'flex';
        } else {
            if (badge) badge.remove();
            if (floatBtn) floatBtn.style.display = 'none';
        }
    }

    updateTotal() {
        const total = this.cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
        const totalEl = document.querySelector('.cart-total-value');
        if (totalEl) totalEl.innerText = `${total.toLocaleString()} с`;

        const footer = document.querySelector('.cart-footer');
        if (footer) footer.style.display = this.cart.length > 0 ? 'block' : 'none';
    }

    toggleCart(active) {
        document.querySelector('.cart-overlay')?.classList.toggle('active', active);
        if (active) this.renderCartItems();
    }

    renderFloatButton() {
        if (document.querySelector('.cart-float-btn')) return;
        const btn = document.createElement('button');
        btn.className = 'cart-float-btn';
        btn.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="9" cy="21" r="1"></circle>
                <circle cx="20" cy="21" r="1"></circle>
                <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
            </svg>
        `;
        document.body.appendChild(btn);
    }

    renderCartDrawer() {
        if (document.querySelector('.cart-overlay')) return;
        const overlay = document.createElement('div');
        overlay.className = 'cart-overlay';
        overlay.innerHTML = `
            <div class="cart-drawer">
                <div class="cart-header">
                    <h2>Ваша корзина</h2>
                    <button class="cart-close">&times;</button>
                </div>
                <div class="cart-items"></div>
                <div class="cart-footer">
                    <div class="cart-total">
                        <span>Итого:</span>
                        <span class="cart-total-value">0 с</span>
                    </div>
                    <button class="cart-whatsapp-btn">
                        <span>Заказать через WhatsApp</span>
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        this.renderCartItems();
    }

    renderCartItems() {
        const container = document.querySelector('.cart-items');
        if (!container) return;

        if (this.cart.length === 0) {
            container.innerHTML = `
                <div class="cart-empty">
                    <span>🛒</span>
                    <p>Корзина пуста</p>
                    <small>Выберите товары в меню</small>
                </div>
            `;
            return;
        }

        container.innerHTML = this.cart.map(item => `
            <div class="cart-item" data-id="${item.id}">
                <img src="${item.image}" alt="${item.name}" class="cart-item-img">
                <div class="cart-item-info">
                    <h4>${item.name}</h4>
                    <div class="cart-item-price">${item.price.toLocaleString()} с</div>
                    <div class="cart-item-actions">
                        <button class="qty-btn qty-minus">-</button>
                        <span class="cart-item-qty">${item.qty}</span>
                        <button class="qty-btn qty-plus">+</button>
                        <button class="cart-item-remove">Удалить</button>
                    </div>
                </div>
            </div>
        `).join('');
        this.updateTotal();
    }

    checkoutWhatsApp() {
        if (this.cart.length === 0) return;

        let message = `🛒 *Новый заказ из Abak Market*\n\n`;
        this.cart.forEach((item, index) => {
            message += `${index + 1}. *${item.name}*\n`;
            message += `   ${item.qty} шт. × ${item.price} с = ${item.qty * item.price} с\n\n`;
        });

        const total = this.cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
        message += `💰 *Итого: ${total} с*`;

        const encodedMsg = encodeURIComponent(message);
        const url = `https://wa.me/${this.whatsappNumber}?text=${encodedMsg}`;
        window.open(url, '_blank');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.cart = new ShoppingCart();
});
