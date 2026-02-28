import { expect, test } from '@playwright/test'

test('create and complete a note', async ({ page }) => {
  const uniqueTitle = `CI note ${Date.now()}`

  await page.goto('/')

  await page.getByTestId('note-input').fill(uniqueTitle)
  await page.getByTestId('add-note-button').click()

  const noteRow = page.getByTestId('note-item').filter({ hasText: uniqueTitle })
  await expect(noteRow).toBeVisible()

  await noteRow.getByRole('button', { name: /mark done/i }).click()
  await expect(noteRow).toHaveAttribute('data-done', 'true')
})
