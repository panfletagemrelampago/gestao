function iniciarGPS() {

    if (!navigator.geolocation) {
        alert("GPS não suportado neste dispositivo")
        return
    }

    console.log("GPS iniciado")

    navigator.geolocation.watchPosition(
        enviarPosicao,
        erroGPS,
        {
            enableHighAccuracy: true,
            maximumAge: 2000,
            timeout: 10000
        }
    )
}

let ultimoEnvio = 0

function enviarPosicao(position){

    const agora = Date.now()

    if(agora - ultimoEnvio < 5000){
        return
    }

    ultimoEnvio = agora

    const latitude = position.coords.latitude
    const longitude = position.coords.longitude
    const accuracy = position.coords.accuracy

    // filtro de precisão
    if(accuracy > 40){
        console.log("GPS ignorado por baixa precisão:", accuracy)
        return
    }

    console.log("Enviando posição:", latitude, longitude)

    fetch("/api/gps", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            latitude: latitude,
            longitude: longitude,
            accuracy: accuracy
        })
    })
    .then(response => {
        if(!response.ok){
            console.error("Erro ao enviar GPS")
        }
    })
    .catch(error => {
        console.error("Erro de conexão:", error)
    })
}

function erroGPS(err){

    console.log("Erro GPS:", err)

    if(err.code === 1){
        alert("Permissão de GPS negada")
    }

    if(err.code === 2){
        console.log("GPS indisponível")
    }

    if(err.code === 3){
        console.log("Timeout ao obter GPS")
    }

}