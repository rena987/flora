export default function ImageUploader({ onImageSelect, imagePreview, onClear }) {
  return (
    <>
      {imagePreview ? (
        <div style={{ position: "relative", flexShrink: 0 }}>
          <img src={`data:image/jpeg;base64,${imagePreview}`} className="image-preview-thumb" alt="preview" />
          <button
            onClick={onClear}
            style={{
              position: "absolute", top: -6, right: -6,
              background: "#c97b7b", border: "none", borderRadius: "50%",
              width: 18, height: 18, cursor: "pointer",
              color: "white", fontSize: "0.6rem", display: "flex",
              alignItems: "center", justifyContent: "center"
            }}
          >✕</button>
        </div>
      ) : (
        <label className={`upload-btn`}>
          📎
          <input
            type="file"
            accept="image/*"
            onChange={onImageSelect}
          />
        </label>
      )}
    </>
  )
}