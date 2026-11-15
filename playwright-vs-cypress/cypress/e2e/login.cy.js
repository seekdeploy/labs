describe('login', () => {
  it('signs in with the right password', () => {
    cy.visit('/');
    cy.get('input[name=email]').type('ada@example.com');
    cy.get('input[name=password]').type('hunter2');
    cy.contains('button', 'Sign in').click();
    cy.get('[role=status]').should('have.text', 'Welcome, ada@example.com');
  });
});
