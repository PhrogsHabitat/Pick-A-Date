// This is your test secret API key.
const stripe = Stripe("rk_test_51QJ3wRCpRmcr6sEEmKahNgqFjDOreuGrSTW9pMlNH4BMjPcfJOWbmsaxKOPkSj8tNjhKzjGcyLUs8PoOsAb07p8s008wNu9UXY");

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