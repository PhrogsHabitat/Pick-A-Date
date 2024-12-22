// This is your test secret API key.
const stripe = Stripe("pk_test_51QJ3wRCpRmcr6sEE7Y6BtDOtKhHL8z9Cycx0RneVX5F4vB4ohLRf6wl778pO6KY1myaz8rNI2vua6oV09ZAxeacc00QEc5BKZP");

initialize();

// Create a Checkout Session
async function initialize() {
  const fetchClientSecret = async () => {
    const response = await fetch("/create-checkout-session", {
      method: "POST",
    });
    const { clientSecret } = await response.json();
    return clientSecret;
  };

  const checkout = await stripe.initEmbeddedCheckout({
    fetchClientSecret,
  });

  // Mount Checkout
  checkout.mount('#checkout');
}