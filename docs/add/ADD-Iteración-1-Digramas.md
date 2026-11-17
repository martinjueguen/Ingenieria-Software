## Diagrama de modulos: 

<img width="818" height="1222" alt="image" src="https://github.com/user-attachments/assets/bcaaee38-e5e5-4f07-8373-111cd576e0e8" />


La arquitectura se organiza en tres capas: el cliente, que proporciona las interfaces web y móvil; el servidor de aplicaciones, que concentra la lógica de negocio, las integraciones, la seguridad y el procesamiento asincrónico; y la capa de datos, que almacena la información en una base de datos independiente. El servidor se comunica con los servicios externos mediante APIs y con la base de datos mediante operaciones de lectura y escritura.

---

## Diagrama de componentes y conectores:

<img width="611" height="1634" alt="image" src="https://github.com/user-attachments/assets/adb8c889-11e1-4d8f-a474-d4233d9baba5" />

En este diagrama, las flechas representan los conectores de comunicación. Las solicitudes entre el cliente y el servidor son sincrónicas, mientras que los eventos enviados al bus se procesan asincrónicamente.