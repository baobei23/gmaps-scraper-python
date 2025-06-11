/**
 * @typedef {import('botasaurus-controls').Controls} Controls
 * @typedef {import('botasaurus-controls').FileTypes} FileTypes
 * 
 */

/**
 * @param {Controls} controls
 */
function getInput(controls) {
    controls
        .listOfTexts('queries', { 
            label: 'Kata Kunci Pencarian (satu per baris)', 
            placeholder: 'misalnya, Restoran di Jakarta', 
            defaultValue: ['Hotel di Padang'],
            isDisabled: (data) => data.use_categories,
            disabledMessage: 'Dinonaktifkan jika "Gunakan Pencarian Kategori" aktif.'
        })
        .switch('use_categories', {
            label: 'Gunakan Pencarian Kategori (menonaktifkan input manual di atas)',
            defaultValue: false,
            helpText: 'Jika diaktifkan, pencarian akan dilakukan berdasarkan semua kategori Google Maps untuk lokasi yang ditentukan di bawah ini.'
        })
        .text('category_location', {
            label: 'Lokasi untuk Pencarian Kategori',
            placeholder: 'misalnya, Padang',
            isRequired: (data) => data.use_categories,
            isDisabled: (data) => !data.use_categories,
            disabledMessage: 'Diaktifkan hanya jika "Gunakan Pencarian Kategori" aktif.',
            helpText: 'Masukkan nama daerah (kota, provinsi, dll.).'
        })
        .number('max_categories', {
            label: 'Batas Jumlah Kategori (opsional)',
            placeholder: 'misalnya, 100',
            helpText: 'Batasi jumlah kategori yang akan digunakan untuk pencarian. Biarkan kosong untuk menggunakan semua kategori.',
            min: 1,
            isShown: (data) => data.use_categories,
            isDisabled: (data) => !data.use_categories,
            isRequired: false
        });
}
